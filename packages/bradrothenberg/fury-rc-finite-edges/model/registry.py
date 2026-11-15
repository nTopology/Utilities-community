"""Part registry, mesh cache and preview driver shared by the model scripts."""
from __future__ import annotations
import hashlib, time
from pathlib import Path
import numpy as np
import fieldlab as fl

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.local' / 'meshcache'
fl.LUT_DIR = ROOT / '.local' / 'lut'

# preview colour, roughness, metallic (the RTX render has its own material table)
MAT = {
    'skin': ((0.63, 0.65, 0.67), 0.55, 0.0),            # light gull gray, FS 36375-like
    'skin_b': ((0.60, 0.62, 0.645), 0.55, 0.0),         # panel-to-panel tone variation
    'skin_c': ((0.655, 0.67, 0.69), 0.55, 0.0),
    'skin_dark': ((0.47, 0.49, 0.52), 0.55, 0.0),       # darker gray edges / radome
    'door': ((0.61, 0.63, 0.655), 0.55, 0.0),
    'control': ((0.62, 0.64, 0.665), 0.55, 0.0),
    'seal': ((0.07, 0.07, 0.075), 0.7, 0.0),
    'walk': ((0.16, 0.17, 0.18), 0.8, 0.0),
    'exhaust': ((0.20, 0.17, 0.14), 0.45, 0.8),         # heat-stained titanium / ceramic tiles
    'exhaust_dark': ((0.045, 0.043, 0.04), 0.6, 0.5),
    'duct': ((0.82, 0.82, 0.80), 0.5, 0.0),             # white inlet duct
    'antenna': ((0.86, 0.87, 0.86), 0.45, 0.0),
    'lens_red': ((0.75, 0.10, 0.05), 0.2, 0.0),
    'lens_green': ((0.05, 0.65, 0.30), 0.2, 0.0),
    'lens_clear': ((0.85, 0.88, 0.9), 0.1, 0.0),
    'glass_dark': ((0.02, 0.025, 0.03), 0.08, 0.0),
    'primer': ((0.52, 0.60, 0.36), 0.6, 0.0),           # structure: yellow-green primer
    'alu': ((0.72, 0.73, 0.74), 0.35, 0.9),
    'titanium': ((0.50, 0.48, 0.45), 0.4, 0.9),
    'composite': ((0.09, 0.09, 0.095), 0.45, 0.1),      # bare carbon / epoxy
    'steel': ((0.42, 0.43, 0.45), 0.3, 1.0),
    'engine': ((0.55, 0.55, 0.56), 0.35, 0.9),
    'engine_hot': ((0.36, 0.30, 0.25), 0.4, 0.9),
    'tank': ((0.20, 0.22, 0.25), 0.6, 0.0),
    'white': ((0.90, 0.90, 0.88), 0.4, 0.0),
    'rubber': ((0.03, 0.03, 0.03), 0.9, 0.0),
    'hyd': ((0.75, 0.76, 0.78), 0.2, 1.0),
    'weapon': ((0.36, 0.40, 0.33), 0.5, 0.0),
    'avionics': ((0.12, 0.12, 0.13), 0.5, 0.2),
    'wire': ((0.85, 0.45, 0.10), 0.5, 0.0),
    'trim': ((0.62, 0.47, 0.22), 0.35, 0.9),            # heat-tinted exhaust lip trim
}


class Part:
    def __init__(self, name, field, mat, section, lo, hi, h, group):
        self.name, self.field, self.mat, self.section = name, fl.lift(field), mat, section
        self.lo, self.hi, self.h, self.group = [float(v) for v in lo], [float(v) for v in hi], float(h), group

    def key(self):
        memo = {}
        for n in fl._topo([self.field]):
            if n.op == 'guide':
                v = ('g', n.val.u0, n.val.u1, tuple(round(c, 12) for c in n.val.ctrl))
            else:
                v = n.val
            memo[n.uid] = hashlib.md5(repr((n.op, v, tuple(memo[a.uid] for a in n.args))).encode()).hexdigest()
        return memo[self.field.uid]


class Aircraft:
    def __init__(self):
        self.parts: list[Part] = []
        self.names = set()

    def add(self, name, field, mat, section, lo, hi, h=0.006, group=None):
        assert name not in self.names, name
        self.names.add(name)
        self.parts.append(Part(name, field, mat, section, lo, hi, h, group or section))
        return field

    def add_pair(self, name, field, mat, section, lo, hi, h=0.006, group=None):
        """Field symmetric in y (built on |y|) registered as separate right (+y) and left bodies."""
        lo, hi = list(lo), list(hi)
        ylo = max(lo[1], -0.002)
        self.add('Right ' + name, fl.fmax(field, -fl.Y), mat, section, [lo[0], ylo, lo[2]], hi, h, group)
        self.add('Left ' + name, fl.fmax(field, fl.Y), mat, section, [lo[0], -hi[1], lo[2]], [hi[0], -ylo, hi[2]], h, group)
        return field

    def select(self, groups=None):
        if not groups:
            return self.parts
        return [p for p in self.parts if any(g.lower() in p.group.lower() or g.lower() in p.name.lower() for g in groups)]


def mesh_part(part: Part, scale=1.0, verbose=True):
    """Preview mesh with cache keyed by graph structure, bounds and resolution."""
    CACHE.mkdir(parents=True, exist_ok=True)
    h = part.h * scale
    key = hashlib.md5(repr((part.key(), part.lo, part.hi, round(h, 6), 'relax3')).encode()).hexdigest()
    file = CACHE / (key + '.npz')
    if file.exists():
        d = np.load(file)
        return d['v'], d['f'], d['n']
    t = time.time()
    v, f, n = fl.mesh_field(part.field, part.lo, part.hi, h)
    np.savez(file, v=v, f=f, n=n)
    if verbose:
        touch = ''
        if len(v):
            lo, hi = v.min(0), v.max(0)
            edge = [ax for i, ax in enumerate('xyz') if lo[i] - part.lo[i] < h * 1.5 or part.hi[i] - hi[i] < h * 1.5]
            touch = (' TOUCHES BBOX ' + ''.join(edge)) if edge else ''
        print(f'  meshed {part.name}: {len(f)} tris, nodes {fl.node_count(part.field)}, {time.time() - t:.1f}s{touch}', flush=True)
    return v, f, n


# ---------------------------------------------------------------------------- skin panels cut from one surface mesh
def surface_mesh(field, lo, hi, h, tag='surface', verbose=True):
    """Mesh of the starboard half of a closed body, open on the symmetry plane y = lo[1] (vertices pinned to it).
    Cached like the part meshes."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = Part(tag, field, 'skin', '', lo, hi, h, '')
    key = hashlib.md5(repr((p.key(), p.lo, p.hi, round(h, 6), 'half pin_y0 relax3')).encode()).hexdigest()
    file = CACHE / (key + '.npz')
    if file.exists():
        d = np.load(file)
        return d['v'], d['f'], d['n']
    t = time.time()
    v, f, n = fl.mesh_field(field, p.lo, p.hi, h, pin_y0=True)
    np.savez(file, v=v, f=f, n=n)
    if verbose:
        print(f'  meshed {tag}: {len(f)} tris at h = {h * 1000:.1f} mm, {time.time() - t:.0f}s', flush=True)
    return v, f, n


def values_at(field, pts, chunk=1_500_000):
    """Field values at points (numpy in, numpy out)."""
    import torch
    out = []
    with torch.no_grad():
        for i in range(0, len(pts), chunk):
            p = torch.tensor(np.ascontiguousarray(pts[i:i + chunk]), dtype=torch.float32, device=fl.DEV)
            out.append(fl.evaluate(field, p[:, 0], p[:, 1], p[:, 2]).cpu().numpy())
    return np.concatenate(out) if out else np.zeros(0, np.float32)


def clip_surface(V, N, F, s, depth=0.0):
    """The part of a triangle mesh where the vertex scalar s is negative, cut along s = 0 (linear along the edges),
    with a wall of the given depth along the cut, hanging from the cut edge against the vertex normal: the edge of a
    panel of that thickness. Returns v, f, n."""
    inside = s < 0
    cnt = inside[F].sum(1)
    full = F[cnt == 3]
    X = F[(cnt == 1) | (cnt == 2)]
    if len(full) == 0 and len(X) == 0:
        return np.zeros((0, 3), np.float32), np.zeros((0, 3), np.int32), np.zeros((0, 3), np.float32)
    if len(X) == 0:
        used = np.unique(full)
        remap = np.full(len(V), -1, np.int64)
        remap[used] = np.arange(len(used))
        return V[used].astype(np.float32), remap[full].astype(np.int32), N[used].astype(np.float32)
    ins = inside[X]
    one = ins.sum(1) == 1
    odd = np.where(one, ins.argmax(1), (~ins).argmax(1))            # the vertex alone on its side
    r = np.arange(len(X))
    a, b, c = X[r, odd], X[r, (odd + 1) % 3], X[r, (odd + 2) % 3]

    def cut(i, j):
        t = (s[i] / (s[i] - s[j]))[:, None].astype(np.float64)
        p = V[i] + t * (V[j] - V[i])
        n = N[i] + t * (N[j] - N[i])
        return p, n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]

    pab, nab = cut(a, b)
    pac, nac = cut(a, c)
    # edge points are shared between the two triangles on an edge
    ek = np.r_[np.c_[np.minimum(a, b), np.maximum(a, b)], np.c_[np.minimum(a, c), np.maximum(a, c)]]
    _, first, inv = np.unique(ek[:, 0].astype(np.int64) * len(V) + ek[:, 1], return_index=True, return_inverse=True)
    EP, EN = np.r_[pab, pac][first], np.r_[nab, nac][first]
    used = np.unique(np.r_[full.ravel(), a[one], b[~one], c[~one]])
    remap = np.full(len(V), -1, np.int64)
    remap[used] = np.arange(len(used))
    nv = len(used)
    iab, iac = nv + inv[:len(X)], nv + inv[len(X):]
    t1 = np.c_[remap[a[one]], iab[one], iac[one]]                   # one vertex inside: the corner triangle
    t2 = np.c_[iab[~one], remap[b[~one]], remap[c[~one]]]           # two inside: the quad ab, b, c, ac
    t3 = np.c_[iab[~one], remap[c[~one]], iac[~one]]
    v = np.r_[V[used], EP]
    n = np.r_[N[used], EN]
    f = np.r_[remap[full], t1, t2, t3]
    if depth > 0:
        # cut segments with the panel on their left seen from outside: ab -> ac (one inside), ac -> ab (two inside)
        p0 = np.r_[iab[one], iac[~one]]
        q0 = np.r_[iac[one], iab[~one]]
        P, Q, NP, NQ = v[p0], v[q0], n[p0], n[q0]
        P2, Q2 = P - depth * NP, Q - depth * NQ
        wn = np.cross(Q - P, 0.5 * (NP + NQ))                       # out of the panel, into the gap
        wn /= np.maximum(np.linalg.norm(wn, axis=1), 1e-12)[:, None]
        m, k = len(P), len(v)
        v = np.r_[v, Q, P, P2, Q2]
        n = np.r_[n, wn, wn, wn, wn]
        i = np.arange(m)
        f = np.r_[f, np.c_[k + i, k + m + i, k + 2 * m + i], np.c_[k + i, k + 2 * m + i, k + 3 * m + i]]
    return v.astype(np.float32), f.astype(np.int32), n.astype(np.float32)


def mirror_mesh(v, f, n):
    return v * np.array([1, -1, 1], np.float32), f[:, ::-1].copy(), n * np.array([1, -1, 1], np.float32)


def join_meshes(a, b):
    return np.r_[a[0], b[0]], np.r_[a[1], b[1] + len(a[0])].astype(np.int32), np.r_[a[2], b[2]]


def orient_faces(F):
    """Turn triangles so that every pair of neighbours runs along its shared edge in opposite directions.

    The surface mesher leaves a few thousand triangles along the sharp wing and tail edges turned the wrong way. The mesh is
    still closed, but the flow solver takes the inside / outside sign from the triangle normals: with those triangles in it, it
    marked blocks of open air behind the trailing edges as solid (found 2026-11-15 in the saved flow field), which spoiled every
    flow run made before that. Returns the faces, how many were turned and how many edges still clash (0 for an orientable surface).
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import breadth_first_order
    n = len(F)
    e = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
    tri = np.tile(np.arange(n), 3)
    fwd = e[:, 0] < e[:, 1]
    key = np.minimum(e[:, 0], e[:, 1]).astype(np.int64) * (int(F.max()) + 1) + np.maximum(e[:, 0], e[:, 1])
    order = np.argsort(key, kind='stable')
    key, tri, fwd = key[order], tri[order], fwd[order]
    pair = np.nonzero(key[1:] == key[:-1])[0]
    ta, tb = tri[pair], tri[pair + 1]
    same = fwd[pair] == fwd[pair + 1]                      # both run the same way along the edge: one of the two must be turned
    g = coo_matrix((np.ones(len(ta)), (ta, tb)), shape=(n, n)).tocsr()
    g = g + g.T
    flip = np.zeros(n, bool)
    seen = np.zeros(n, bool)
    par = {}
    for a_, b_, s_ in zip(ta[same], tb[same], same[same]):
        par[(min(a_, b_), max(a_, b_))] = True
    for seed in range(n):
        if seen[seed]:
            continue
        nodes, pred = breadth_first_order(g, seed, directed=False)
        seen[nodes] = True
        for k in nodes[1:]:
            q = pred[k]
            flip[k] = flip[q] ^ ((min(k, q), max(k, q)) in par)
        if seed == 0 and seen.all():
            break
    clash = int(np.sum((flip[ta] ^ flip[tb]) != same))
    if flip.sum() > n / 2:
        flip = ~flip
    out = F.copy()
    out[flip] = out[flip][:, ::-1]
    return out, int(flip.sum()), clash
