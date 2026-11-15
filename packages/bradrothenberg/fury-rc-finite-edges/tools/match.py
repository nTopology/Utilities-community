"""Overlay the model silhouette on reference photographs.

  match.py <mesh npz> <out folder> [view ...]

Each photograph is rectified into the model frame (an affine map found from a few picked points:
nose, tail, wing tips), drawn with fuselage length = K pixels, and the model silhouette is drawn on it.
The silhouette of the photograph (aircraft against the sky) is segmented by colour where the
background allows it, and compared with the model: overlap (intersection over union) and the
distance between the two outlines as a percentage of the fuselage length.

The picked points are in reference/match_views.json (pixels of the original files).
"""
import json, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
K = 1500                                   # pixels per fuselage length in the rectified pictures
VIEWS = json.loads((ROOT / 'reference' / 'match_views.json').read_text())


def frame(view):
    """Returns (origin px, e1 px per length along the first model axis, e2 px per length along the second)."""
    v = VIEWS[view]
    n, t = np.array(v['nose'], float), np.array(v['tail'], float)
    if v['kind'] == 'plan':
        # model axes: x/L aft, y/L to the side. Wing tips give the span direction; semi_span is b/2L.
        b = (np.array(v['tip_a'], float) - np.array(v['tip_b'], float)) / 2 / v['semi_span']
        return n, t - n, b
    # side: model axes x/L aft, z/L up. The tail point is the centre of the nozzle exit, tail_z above the reference line.
    d = t - n
    k = v['tail_z']
    best = None
    for sgn in (1.0, -1.0):
        R = np.array([[0.0, -sgn], [sgn, 0.0]])
        e1 = np.linalg.solve(np.eye(2) + k * R, d)
        e2 = R @ e1
        if e2[1] < 0:                      # model up is up in the picture
            best = (n, e1, e2)
    return best


def rectify(view, lo, hi, white=False):
    """Photograph resampled so that output pixel (u, v) is model (lo[0] + u/K, hi[1] - v/K)."""
    v = VIEWS[view]
    o, e1, e2 = frame(view)
    im = Image.open(ROOT / 'reference' / 'public' / v['file']).convert('RGB')
    if white:
        im = Image.new('RGB', im.size, (255, 255, 255))
    size = (int((hi[0] - lo[0]) * K), int((hi[1] - lo[1]) * K))
    # input = o + (lo0 + u/K) e1 + (hi1 - v/K) e2
    c = o + lo[0] * e1 + hi[1] * e2
    data = (e1[0] / K, -e2[0] / K, c[0], e1[1] / K, -e2[1] / K, c[1])
    return im.transform(size, Image.AFFINE, data, resample=Image.BICUBIC)


def silhouette(mesh, axes, lo, hi):
    """Mask of the mesh seen along the third axis. axes: the two model axes shown (0 = x, 1 = y, 2 = z)."""
    v, f, L = mesh
    size = (int((hi[0] - lo[0]) * K), int((hi[1] - lo[1]) * K))
    p = np.c_[(v[:, axes[0]] / L - lo[0]) * K, (hi[1] - v[:, axes[1]] / L) * K]
    img = Image.new('L', size, 0)
    d = ImageDraw.Draw(img)
    tri = p[f].reshape(len(f), 6)
    keep = (np.abs(tri[:, 0] * (tri[:, 3] - tri[:, 5]) + tri[:, 2] * (tri[:, 5] - tri[:, 1]) + tri[:, 4] * (tri[:, 1] - tri[:, 3])) > 0.05)
    for t in tri[keep]:
        d.polygon(t.tolist(), fill=255)
    return np.asarray(img) > 0


def outline(mask):
    m = Image.fromarray((mask * 255).astype(np.uint8))
    return (np.asarray(m.filter(ImageFilter.MaxFilter(5))) > 0) & ~(np.asarray(m.filter(ImageFilter.MinFilter(3))) > 0)


def photo_mask(img, view, model_mask, valid):
    """Aircraft against a plain sky. The sky colour is a plane fitted through the pixels well away from the model
    silhouette; the aircraft is what differs from it by more than the threshold. None when the background is not plain."""
    v = VIEWS[view]
    if not v.get('sky'):
        return None
    from scipy import ndimage
    a = np.asarray(img).astype(np.float32)
    a = ndimage.uniform_filter(a, size=(5, 5, 1))
    h, w = a.shape[:2]
    far = valid & ~ndimage.binary_dilation(model_mask, iterations=int(0.05 * K))
    yy, xx = np.nonzero(far)
    pick = np.random.default_rng(0).choice(len(yy), min(len(yy), 200_000), replace=False)
    A = np.c_[np.ones(len(pick)), xx[pick] / w, yy[pick] / h, (xx[pick] / w) ** 2, (yy[pick] / h) ** 2]
    coef = np.linalg.lstsq(A, a[yy[pick], xx[pick]], rcond=None)[0]
    gy, gx = np.mgrid[0:h, 0:w]
    sky = np.stack([np.ones_like(gx, float), gx / w, gy / h, (gx / w) ** 2, (gy / h) ** 2], -1) @ coef
    d = np.linalg.norm(a - sky, axis=2)
    m = (d > v['sky']) & valid
    m = ndimage.binary_closing(ndimage.binary_opening(m, iterations=2), iterations=4)
    lab, n = ndimage.label(m)
    if n == 0:
        return None
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(sizes)))
    return ndimage.binary_fill_holes(m)


def compare(view, mesh, out):
    v = VIEWS[view]
    lo, hi = v['window'][:2], v['window'][2:]
    axes = (0, 1) if v['kind'] == 'plan' else (0, 2)
    img = rectify(view, lo, hi)
    mm = silhouette(mesh, axes, lo, hi)
    if v['kind'] == 'plan':
        mm = mm | mm[::-1] if abs(lo[1] + hi[1]) < 1e-9 else mm
    a = np.asarray(img).copy()
    edge = outline(mm)
    a[edge] = (255, 120, 0)
    res = dict(view=view, file=v['file'])
    valid = np.asarray(rectify(view, lo, hi, white=True))[:, :, 0] > 250
    pm = photo_mask(img, view, mm, valid)
    if pm is not None:
        box = v.get('score_window')
        sel = np.ones_like(mm)
        if box:                                # leave out the nose boom, stores and landing gear
            sel[:] = False
            sel[int((hi[1] - box[3]) * K):int((hi[1] - box[1]) * K), int((box[0] - lo[0]) * K):int((box[2] - lo[0]) * K)] = True
        inter, union = (mm & pm & sel).sum(), ((mm | pm) & sel).sum()
        res['overlap_iou'] = round(float(inter / max(union, 1)), 4)
        from scipy.ndimage import distance_transform_edt
        pe = outline(pm) & sel
        dist_to_model = distance_transform_edt(~outline(mm))
        dist_to_photo = distance_transform_edt(~outline(pm))
        d1 = dist_to_model[pe] / K * 100
        d2 = dist_to_photo[edge & sel] / K * 100
        res['outline_distance_percent_length'] = dict(photo_to_model_median=round(float(np.median(d1)), 3), photo_to_model_p90=round(float(np.quantile(d1, 0.9)), 3),
                                                      model_to_photo_median=round(float(np.median(d2)), 3), model_to_photo_p90=round(float(np.quantile(d2, 0.9)), 3))
        a[outline(pm) & ~edge] = (0, 230, 255)
    Image.fromarray(a).save(out / f'{view}.jpg', quality=90)
    return res


if __name__ == '__main__':
    d = np.load(sys.argv[1])
    L = float(d['L']) if 'L' in d else 9.144
    mesh = (d['v'], d['f'], L)
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    results = [compare(view, mesh, out) for view in (sys.argv[3:] or VIEWS)]
    (out / 'match.json').write_text(json.dumps(results, indent=1))
    for r in results:
        print(json.dumps(r))
