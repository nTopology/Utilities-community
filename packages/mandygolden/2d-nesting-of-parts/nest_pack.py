"""Packer for the nTop "Nest Parts" custom block.

The block writes, into its Work Folder:
  parts.csv          one row per body: minx,miny,maxx,maxy (shadow bounds, mm), minz,maxz (body)
  shadow_<i>         nTop slice-image archive (a zip holding slice_1.png) of body i's shadow,
                     rendered over that body's shadow bounds; white = inside
  params.csv         one column "param": spacing, lift, rot_step, px0, py0, px1, py1, pz0, margin
and then runs:
  nest_pack.py <folder>                      (parameters from params.csv), or
  nest_pack.py <folder> <spacing> <lift> <rot_step> <px0> <py0> <px1> <py1> <pz0> <margin>
This script writes placements0.csv (angle_deg,dx,dy,dz,placed; one row per body, same order)
and prints its path. Each body is rotated about the Z axis through the world origin by angle_deg,
then translated by (dx,dy,dz). Bodies that do not fit are parked in a row beside the plate's +X
edge (placed = 0) and listed in unplaced.csv, so the run still succeeds and the rest can go on a
second plate.

Nesting: bottom-left fill on a boolean occupancy grid, a sweep of rotations, several part
orders, choosing the layout with the smallest nest bounding box. The raster step, the number
of orders and the rotation sweep adapt to the part count and size so a run stays within a few
minutes; BUDGET_S caps the search and keeps the best layout found so far.
"""
import csv, io, itertools, math, os, sys, time, zipfile
import numpy as np
from PIL import Image

BUDGET_S = 240.0      # stop trying new orders after this many seconds, keep the best so far
MAX_CELLS = 220       # largest part spans about this many cells; the step grows for big parts
MIN_STEP = 0.5        # mm

folder = sys.argv[1]
if len(sys.argv) >= 10:
    vals = [float(v) for v in sys.argv[2:11]]
else:
    # the block writes params.csv (one column "param": spacing, lift, rot_step, px0, py0, px1, py1,
    # pz0, margin) so that the command line nTop runs never changes with the parameters
    with open(os.path.join(folder, "params.csv"), newline="") as fh:
        vals = [float(r["param"]) for r in csv.DictReader(fh)]
while len(vals) < 9:
    vals.append(0.0)
spacing, lift, rot_step, px0, py0, px1, py1, pz0, margin = vals[:9]
t_start = time.time()
log = open(os.path.join(folder, "nest_pack.log"), "w")


def say(*a):
    print(*a, file=log); log.flush()


say("args:", sys.argv[1:])

# ---- read the parts table and pick the raster step ---------------------------------------------
rows = list(csv.DictReader(open(os.path.join(folder, "parts.csv"), newline="")))
spans = [max(float(r["maxx"]) - float(r["minx"]), float(r["maxy"]) - float(r["miny"])) for r in rows]
STEP = max(MIN_STEP, max(spans) / MAX_CELLS)
STEP = math.ceil(STEP * 4) / 4.0          # round up to a quarter millimetre
say("bodies: %d, largest span %.1f mm, raster step %.2f mm" % (len(rows), max(spans), STEP))

parts = []
for i, r in enumerate(rows):
    minx, miny, maxx, maxy = (float(r[k]) for k in ("minx", "miny", "maxx", "maxy"))
    minz, maxz = float(r["minz"]), float(r["maxz"])
    path = os.path.join(folder, "shadow_%d" % i)   # nTop writes a zip archive; the block names it without an extension
    with zipfile.ZipFile(path) as z:
        names = sorted(z.namelist())
        img = Image.open(io.BytesIO(z.read(names[0]))).convert("L")
    a = np.asarray(img, dtype=np.uint8)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    inside_is_white = (border > 127).mean() < 0.5
    mask_img = (a > 127) if inside_is_white else (a <= 127)
    H, W = mask_img.shape
    nx = int(math.ceil((maxx - minx) / STEP)) + 1
    ny = int(math.ceil((maxy - miny) / STEP)) + 1
    xs = minx + np.arange(nx) * STEP
    ys = miny + np.arange(ny) * STEP
    cols = np.clip(((xs - minx) / (maxx - minx) * W).astype(int), 0, W - 1)
    rws = np.clip(((maxy - ys) / (maxy - miny) * H).astype(int), 0, H - 1)
    mask = mask_img[rws[:, None], cols[None, :]]
    d = mask.copy()   # one-cell dilation: the voxel shadow runs slightly small and sampling can drop edge pixels
    d[1:, :] |= mask[:-1, :]; d[:-1, :] |= mask[1:, :]; d[:, 1:] |= mask[:, :-1]; d[:, :-1] |= mask[:, 1:]
    # a round footprint needs no rotation sweep: square bounds and a fill ratio near pi/4
    fill = mask.sum() / float(mask.size)
    roundish = abs((maxx - minx) - (maxy - miny)) < 2 * STEP and abs(fill - math.pi / 4) < 0.04
    parts.append({"i": i, "x0": minx, "y0": miny, "mask": d, "minz": minz, "maxz": maxz,
                  "cx": (minx + maxx) / 2.0, "cy": (miny + maxy) / 2.0, "round": roundish})
    say("part %d: image %dx%d, grid %dx%d, filled %d, z %.2f..%.2f%s" % (i, W, H, nx, ny, int(d.sum()), minz, maxz, ", round" if roundish else ""))

# ---- packing -------------------------------------------------------------------------------------
plate_w = int(round((px1 - px0) / STEP)); plate_h = int(round((py1 - py0) / STEP))
edge = int(round(margin / STEP)); gap = int(round(spacing / STEP))
angles = [k * rot_step for k in range(max(1, int(round(360.0 / rot_step))))] if rot_step > 0 else [0.0]


def rotate(mask, deg):
    h, w = mask.shape
    t = math.radians(deg); c, s = math.cos(t), math.sin(t)
    diag = int(math.ceil(math.hypot(h, w))) + 2
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    oy, ox = np.mgrid[0:diag, 0:diag]
    oy = oy - (diag - 1) / 2.0; ox = ox - (diag - 1) / 2.0
    ix = np.rint(c * ox + s * oy + cx).astype(int); iy = np.rint(-s * ox + c * oy + cy).astype(int)
    ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    out = np.zeros((diag, diag), dtype=bool); out[ok] = mask[iy[ok], ix[ok]]
    ys_, xs_ = np.nonzero(out)
    y0, y1, x0, x1 = ys_.min(), ys_.max(), xs_.min(), xs_.max()
    return out[y0:y1 + 1, x0:x1 + 1], (x0 + x1) / 2.0 - (diag - 1) / 2.0, (y0 + y1) / 2.0 - (diag - 1) / 2.0


def dilate(mask, r):
    if r <= 0:
        return mask.copy()
    h, w = mask.shape
    out = np.zeros((h + 2 * r, w + 2 * r), dtype=bool)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out[r + dy:r + dy + h, r + dx:r + dx + w] |= mask
    return out


def free_positions(occ, mask):
    oh, ow = occ.shape; mh, mw = mask.shape
    if mh > oh or mw > ow:
        return np.zeros((0, 0), dtype=bool)
    fh, fw = oh + mh - 1, ow + mw - 1
    A = np.fft.rfft2(occ.astype(np.float32), s=(fh, fw))
    B = np.fft.rfft2(mask[::-1, ::-1].astype(np.float32), s=(fh, fw))
    corr = np.fft.irfft2(A * B, s=(fh, fw))
    return corr[mh - 1:oh, mw - 1:ow] < 0.5


masks = [p["mask"] for p in parts]
diags = [int(math.ceil(math.hypot(*m.shape))) for m in masks]
span = sum(diags) + 2 * edge + len(masks) * gap
W, H = min(plate_w, span), min(plate_h, span)
rot_cache = [[rotate(m, a) for a in ([0.0] if parts[k]["round"] else angles)] for k, m in enumerate(masks)]
order0 = tuple(sorted(range(len(parts)), key=lambda k: -int(masks[k].sum())))
n = len(parts)
if n <= 4:
    orders = list(itertools.permutations(range(n)))
else:
    rng = np.random.RandomState(7)
    orders = [order0] + [tuple(rng.permutation(n)) for _ in range(5 if n <= 6 else 3)]
say("search: %dx%d cells, %d orders, %d angles, budget %.0f s" % (W, H, len(orders), len(angles), BUDGET_S))

best = None
for oi, order in enumerate(orders):
    if oi > 0 and time.time() - t_start > BUDGET_S:
        say("budget reached after %d orders" % oi); break
    occ = np.zeros((H, W), dtype=bool)
    if edge > 0:
        occ[:edge, :] = True; occ[-edge:, :] = True; occ[:, :edge] = True; occ[:, -edge:] = True
    bbox = [W, H, -1, -1]; layout = []; unplaced = []
    for pi in order:
        # only the region the nest could grow into is searched: the current nest plus this part
        reach = diags[pi] + 2 * gap + 2
        Wi = W if bbox[2] < 0 else min(W, bbox[2] + reach)
        Hi = H if bbox[3] < 0 else min(H, bbox[3] + reach)
        sub_occ = occ[:Hi, :Wi]
        cand = None
        for ai in range(len(rot_cache[pi])):
            crop, _, _ = rot_cache[pi][ai]
            fp = free_positions(sub_occ, crop)
            if fp.size == 0 or not fp.any():
                continue
            ys_, xs_ = np.nonzero(fp); mh, mw = crop.shape
            nx0 = np.minimum(bbox[0], xs_); ny0 = np.minimum(bbox[1], ys_)
            nx1 = np.maximum(bbox[2], xs_ + mw - 1); ny1 = np.maximum(bbox[3], ys_ + mh - 1)
            score = (nx1 - nx0 + 1) * (ny1 - ny0 + 1) * 1000 + (xs_ + ys_)
            k = int(np.argmin(score))
            if cand is None or score[k] < cand[0]:
                cand = (int(score[k]), ai, int(xs_[k]), int(ys_[k]))
        if cand is None:
            # the growth window may be too tight for this part: try the whole plate once
            if Wi < W or Hi < H:
                for ai in range(len(rot_cache[pi])):
                    crop, _, _ = rot_cache[pi][ai]
                    fp = free_positions(occ, crop)
                    if fp.size == 0 or not fp.any():
                        continue
                    ys_, xs_ = np.nonzero(fp); mh, mw = crop.shape
                    nx0 = np.minimum(bbox[0], xs_); ny0 = np.minimum(bbox[1], ys_)
                    nx1 = np.maximum(bbox[2], xs_ + mw - 1); ny1 = np.maximum(bbox[3], ys_ + mh - 1)
                    score = (nx1 - nx0 + 1) * (ny1 - ny0 + 1) * 1000 + (xs_ + ys_)
                    k = int(np.argmin(score))
                    if cand is None or score[k] < cand[0]:
                        cand = (int(score[k]), ai, int(xs_[k]), int(ys_[k]))
            if cand is None:
                unplaced.append(pi); continue        # park it later; keep placing the others
        _, ai, px, py = cand
        crop, _, _ = rot_cache[pi][ai]; mh, mw = crop.shape
        d = dilate(crop, gap); y0, x0 = py - gap, px - gap
        sub = d[max(0, -y0):, max(0, -x0):][:occ.shape[0] - max(0, y0), :occ.shape[1] - max(0, x0)]
        occ[max(0, y0):max(0, y0) + sub.shape[0], max(0, x0):max(0, x0) + sub.shape[1]] |= sub
        bbox = [min(bbox[0], px), min(bbox[1], py), max(bbox[2], px + mw - 1), max(bbox[3], py + mh - 1)]
        layout.append((pi, ai, px, py))
    area = (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1) if layout else 0
    say("order %d: %d of %d placed, nest %.1f x %.1f mm after %.0f s" % (oi, len(layout), n, (bbox[2] - bbox[0] + 1) * STEP if layout else 0, (bbox[3] - bbox[1] + 1) * STEP if layout else 0, time.time() - t_start))
    # most parts placed wins; among equals the smallest nest
    key = (-len(layout), area)
    if best is None or key < best[0]:
        best = (key, layout, bbox, unplaced)

key, layout, bbox, unplaced = best
result = {}
for pi, ai, px, py in layout:
    p = parts[pi]; crop, cx_off, cy_off = rot_cache[pi][ai]; mh, mw = crop.shape
    ang = 0.0 if p["round"] else angles[ai]
    cx, cy = p["cx"], p["cy"]
    land_x = px0 + (px + (mw - 1) / 2.0 - cx_off) * STEP
    land_y = py0 + (py + (mh - 1) / 2.0 - cy_off) * STEP
    dx, dy, dz = land_x - cx, land_y - cy, pz0 + lift - p["minz"]
    t = math.radians(ang); cs, sn = math.cos(t), math.sin(t)
    result[pi] = (ang, cx - (cs * cx - sn * cy) + dx, cy - (sn * cx + cs * cy) + dy, dz)
# parts that did not fit are parked in a row just outside the plate's +X edge, at the same lift,
# unrotated, so they are visibly separate from the nest and ready for a second plate
PARK_GAP = max(spacing, 10.0)
park_x = px1 + PARK_GAP
for pi in sorted(unplaced):
    p = parts[pi]; mh, mw = p["mask"].shape
    w_mm, h_mm = mw * STEP, mh * STEP
    land_x = park_x + w_mm / 2.0
    land_y = py0 + h_mm / 2.0
    result[pi] = (0.0, land_x - p["cx"], land_y - p["cy"], pz0 + lift - p["minz"])
    park_x += w_mm + PARK_GAP
out = os.path.join(folder, "placements0.csv")
with open(out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["angle_deg", "dx", "dy", "dz", "placed"])
    for i in range(len(parts)):
        w.writerow(["%.6f" % v for v in result[i]] + [0 if i in unplaced else 1])
with open(os.path.join(folder, "unplaced.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["index"])
    for pi in sorted(unplaced):
        w.writerow([pi])
if layout:
    say("nest %.1f x %.1f mm in %.0f s, %d of %d parts placed" % ((bbox[2] - bbox[0] + 1) * STEP, (bbox[3] - bbox[1] + 1) * STEP, time.time() - t_start, len(layout), n))
else:
    say("no part fits the plate; all %d parked beside it" % n)
if unplaced:
    say("UNPLACED (parked beside the plate, listed in unplaced.csv): %s" % ", ".join(str(i) for i in sorted(unplaced)))
for i in range(len(parts)):
    say("part %d: angle %.1f move (%.3f, %.3f, %.3f)%s" % ((i,) + result[i] + ("  [parked]" if i in unplaced else "",)))
log.close()
print(out)
