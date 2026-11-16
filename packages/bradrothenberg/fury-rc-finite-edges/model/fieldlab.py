"""fieldlab: one implicit field graph with two back ends.

Every shape is a dimensionless scalar field in meters (negative inside).
The same graph is
  1. evaluated with torch on the GPU for fast preview meshing, and
  2. emitted as a native nTop recipe (plain math blocks, native primitives,
     native splines) for import through the Notebook API.

Coordinates of this project: X aft from the nose tip, Y to starboard, Z up from
the fuselage reference line. Literals are SI (metres).
"""
from __future__ import annotations

import json
import math
import sys
import uuid

from pathlib import Path

import numpy as np
import torch
from scipy.interpolate import BSpline, PPoly

sys.setrecursionlimit(20000)
# Evaluator batch sizes. The defaults keep the process under about 1.5 GB of GPU memory, because the card is shared;
# raise them (FIELDLAB_SLAB=6000000, FIELDLAB_SPLINE=60000000) on a free machine.
import os as _os
SLAB_CELLS = int(_os.environ.get('FIELDLAB_SLAB', 2_000_000))
SPLINE_BUDGET = int(_os.environ.get('FIELDLAB_SPLINE', 24_000_000))
# FIELDLAB_DEVICE=cpu evaluates on the processor: slower per point, but independent of a graphics card that other jobs
# keep busy (there every evaluator call waits for a time slice per kernel).
# FIELDLAB_DEVICE=auto times 300 small kernels on the card when the module loads and takes the processor if they
# need more than 1.5 s (a free card needs about 0.02 s).


def _pick_device():
    want = (_os.environ.get('FIELDLAB_DEVICE') or '').strip().lower()
    if want and want != 'auto':
        return torch.device(want)
    if not torch.cuda.is_available():
        return torch.device('cpu')
    if want == 'auto':
        import time as _time
        try:
            x = torch.zeros(1000, device='cuda')
            float((x + 1.0).sum())
            t = _time.time()
            for _ in range(300):
                x = x * 1.0001 + 1.0
            float(x.sum())
            if _time.time() - t > 1.5:
                return torch.device('cpu')
        except Exception:
            return torch.device('cpu')
    return torch.device('cuda')


DEV = _pick_device()
GRAD_BATCH = int(_os.environ.get('FIELDLAB_GRAD', 400_000))
if DEV.type == 'cpu':                                   # several evaluator processes share the cores: FIELDLAB_THREADS each
    torch.set_num_threads(int(_os.environ.get('FIELDLAB_THREADS', 16)))


# --------------------------------------------------------------------------
# Graph nodes
# --------------------------------------------------------------------------
class F:
    """Hash-consed scalar field node."""
    __slots__ = ('op', 'args', 'val', 'label', 'uid')
    _intern: dict = {}
    _count = 0

    def __new__(cls, op, args=(), val=None):
        args = tuple(args)
        key = (op, tuple(a.uid for a in args), val)
        hit = cls._intern.get(key)
        if hit is not None:
            return hit
        self = object.__new__(cls)
        self.op, self.args, self.val, self.label = op, args, val, None
        cls._count += 1
        self.uid = cls._count
        cls._intern[key] = self
        return self

    # -- naming: a labelled node becomes a named variable in the notebook
    def named(self, label, section=None):
        self.label = label
        if section is not None:
            SECTION[self.uid] = section
        return self

    @property
    def is_const(self):
        return self.op == 'const'

    # -- arithmetic
    def __add__(self, o):
        o = lift(o)
        if self.is_const and o.is_const:
            return const(self.val + o.val)
        if self.is_const and self.val == 0:
            return o
        if o.is_const and o.val == 0:
            return self
        return F('add', (self, o))
    __radd__ = lambda self, o: lift(o).__add__(self)

    def __sub__(self, o):
        o = lift(o)
        if self.is_const and o.is_const:
            return const(self.val - o.val)
        if o.is_const and o.val == 0:
            return self
        return F('sub', (self, o))
    __rsub__ = lambda self, o: lift(o).__sub__(self)

    def __mul__(self, o):
        o = lift(o)
        if self.is_const and o.is_const:
            return const(self.val * o.val)
        if self.is_const and self.val == 1:
            return o
        if o.is_const and o.val == 1:
            return self
        if (self.is_const and self.val == 0) or (o.is_const and o.val == 0):
            return const(0.0)
        if self.is_const:  # keep constants on the right
            return F('mul', (o, self))
        return F('mul', (self, o))
    __rmul__ = lambda self, o: lift(o).__mul__(self)

    def __truediv__(self, o):
        o = lift(o)
        if o.is_const:
            return self * (1.0 / o.val)
        return F('div', (self, o))
    __rtruediv__ = lambda self, o: lift(o).__truediv__(self)

    def __neg__(self):
        return self * -1.0

    def __abs__(self):
        return absf(self)

    def __pow__(self, n):
        if n == 2:
            return self * self
        if n == 3:
            return self * self * self
        if n == 4:
            s = self * self
            return s * s
        if n == 0.5:
            return sqrt(self)
        return powf(self, n)

    def __repr__(self):
        return f'F<{self.op}#{self.uid}>'


SECTION: dict = {}            # node uid -> notebook section of a labelled node
PARAM_SECTION: dict = {}      # input name -> notebook section


def const(v):
    return F('const', (), float(v))


def lift(v):
    return v if isinstance(v, F) else const(v)


X, Y, Z = F('x'), F('y'), F('z')


def param(name, value, section='01 Inputs'):
    """Named design input. A constant on the host, a real variable in nTop. Units go in the name."""
    PARAM_SECTION[str(name)] = section
    return F('param', (), (str(name), float(value)))


def _unary(op, fn):
    def make(a):
        a = lift(a)
        if a.is_const:
            return const(fn(a.val))
        return F(op, (a,))
    return make


absf = _unary('abs', abs)
sqrt = _unary('sqrt', lambda v: math.sqrt(max(v, 0.0)))
sin = _unary('sin', math.sin)
cos = _unary('cos', math.cos)
tan = _unary('tan', math.tan)
exp = _unary('exp', math.exp)


def _nary(op, fn):
    def make(*vals):
        flat = []
        for v in vals:
            v = lift(v)
            if v.op == op:
                flat.extend(v.args)
            else:
                flat.append(v)
        consts = [v.val for v in flat if v.is_const]
        rest = []
        seen = set()
        for v in flat:
            if not v.is_const and v.uid not in seen:
                seen.add(v.uid)
                rest.append(v)
        if consts:
            rest.append(const(fn(consts)))
        if len(rest) == 1:
            return rest[0]
        return F(op, rest)
    return make


fmin = _nary('min', min)
fmax = _nary('max', max)


def clamp(v, lo, hi):
    v, lo, hi = lift(v), lift(lo), lift(hi)
    if v.is_const and lo.is_const and hi.is_const:
        return const(min(max(v.val, lo.val), hi.val))
    return F('clamp', (v, lo, hi))


def mix(a, b, t):
    """a where t=0, b where t=1."""
    a, b, t = lift(a), lift(b), lift(t)
    if t.is_const:
        return a * (1 - t.val) + b * t.val
    if a.is_const and b.is_const and a.val == b.val:
        return a
    return F('mix', (a, b, t))


def atan2(y, x):
    return F('atan2', (lift(y), lift(x)))


def powf(a, b):
    """a ** b for a >= 0."""
    a, b = lift(a), lift(b)
    if a.is_const and b.is_const:
        return const(max(a.val, 1e-9) ** b.val)
    return F('pow', (fmax(a, 1e-9), b))


# -- composites built only from verified basic nodes -----------------------
def saturate(v):
    return clamp(v, 0.0, 1.0)


def smoothstep(e0, e1, v):
    t = saturate((lift(v) - e0) / (e1 - e0))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(e0, e1, v):
    t = saturate((lift(v) - e0) / (e1 - e0))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def smin(a, b, k):
    """Polynomial smooth minimum. k is the blend width in field units."""
    if k <= 0:
        return fmin(a, b)
    a, b = lift(a), lift(b)
    h = fmax(k - absf(a - b), 0.0) * (1.0 / k)
    return fmin(a, b) - h * h * (k * 0.25)


def sminq(a, b, k):
    """Compact quartic smooth minimum, C2 at the edge of its support.

    k is the blend width in field units and may itself be a field, so the blend can
    stay tight in one direction and open in another. The offset where a = b is 3k/16.
    """
    a, b = lift(a), lift(b)
    q = fmax(1.0 - absf(a - b) / k, 0.0)
    return fmin(a, b) - k * (q * q * q) * (4.0 - q) * (1.0 / 16.0)


def smax(a, b, k):
    if k <= 0:
        return fmax(a, b)
    a, b = lift(a), lift(b)
    h = fmax(k - absf(a - b), 0.0) * (1.0 / k)
    return fmax(a, b) + h * h * (k * 0.25)


def union(*bodies, k=0.0):
    out = bodies[0]
    if k <= 0:
        return fmin(*bodies)
    for b in bodies[1:]:
        out = smin(out, b, k)
    return out


def intersect(*bodies, k=0.0):
    out = bodies[0]
    if k <= 0:
        return fmax(*bodies)
    for b in bodies[1:]:
        out = smax(out, b, k)
    return out


def subtract(a, *cutters, k=0.0):
    out = a
    for c in cutters:
        out = smax(out, -lift(c), k)
    return out


def shell(body, thickness):
    """Inward shell: keeps the outer surface."""
    return fmax(body, -(body + thickness))


def length2(a, b):
    return sqrt(a * a + b * b)


def length3(a, b, c):
    return sqrt(a * a + b * b + c * c)


def halfspace(coord, limit, sign=1.0):
    """Negative where sign*(coord-limit) < 0."""
    return (lift(coord) - limit) * sign


def slab(coord, lo, hi):
    c = lift(coord)
    return fmax(lo - c, c - hi)


# --------------------------------------------------------------------------
# Spline DF: signed distance to a planar cubic B-spline whose control points are fields
# --------------------------------------------------------------------------
def spline2d(cps, u, v, label=None):
    """Native Spline DF (spline_implicit). cps: list of (a, b) control point fields in the
    section plane, u, v: the section coordinates of the query point.

    Clamped uniform cubic B-spline. The value is the signed planar distance to the curve,
    positive on the left of the direction of travel (nTop convention), so a body that keeps
    its inside on the right of the curve is negative inside. An open curve is continued by
    straight rays along its end tangents. First point equal to last point makes it closed.
    Control points that vary along the third axis turn the section into a loft.
    """
    cps = [(lift(a), lift(b)) for a, b in cps]
    assert len(cps) >= 4
    args = [lift(u), lift(v)] + [c for pair in cps for c in pair]
    closed = cps[0][0].uid == cps[-1][0].uid and cps[0][1].uid == cps[-1][1].uid
    node = F('spline', args, (3, len(cps), bool(closed)))
    if label:
        node.label = label
    return node


class _SplineBasis:
    """Per-span power-basis matrices of the clamped uniform cubic B-spline with K control points."""
    _cache: dict = {}

    @classmethod
    def get(cls, K, per_span=8):
        key = (K, per_span)
        if key not in cls._cache:
            cls._cache[key] = cls(K, per_span)
        return cls._cache[key]

    def __init__(self, K, per_span):
        ns = K - 3
        knots = np.r_[np.zeros(4), np.arange(1, ns) / ns, np.ones(4)]
        tau = np.array([0.125, 0.375, 0.625, 0.875])
        V = np.vander(tau, 4, increasing=True)
        M = np.zeros((ns, 4, 4))                       # [span, power, local control point]
        for sp in range(ns):
            B = BSpline.design_matrix((sp + tau) / ns, knots, 3).toarray()[:, sp:sp + 4]
            M[sp] = np.linalg.solve(V, B)
        ts = np.linspace(0.0, 1.0, ns * per_span + 1)
        Bs = BSpline.design_matrix(np.clip(ts, 0.0, 1.0 - 1e-12), knots, 3).toarray()
        Bs[-1] = 0.0
        Bs[-1, -1] = 1.0
        self.ns, self.K = ns, K
        self.M = torch.tensor(M, dtype=torch.float64, device=DEV)
        self.ts = torch.tensor(ts, dtype=torch.float64, device=DEV)
        self.Bs = torch.tensor(Bs, dtype=torch.float64, device=DEV)
        self.dt = 1.0 / (ns * per_span)

    def curve(self, P, t, order=0):
        """P (N, K, 2), t (N,) -> point, and derivatives up to `order`, each (N, 2)."""
        ns = self.ns
        sp = torch.clamp((t * ns).floor().long(), 0, ns - 1)
        tau = t * ns - sp
        idx = (sp[:, None] + torch.arange(4, device=P.device)[None, :])[:, :, None].expand(-1, -1, 2)
        Pl = torch.gather(P, 1, idx)                   # (N, 4, 2)
        Ms = self.M.to(P.dtype)[sp]                    # (N, 4 powers, 4 local)
        one = torch.ones_like(tau)
        pw = torch.stack([one, tau, tau * tau, tau * tau * tau], 1)
        out = [torch.einsum('np,npj,njc->nc', pw, Ms, Pl)]
        if order >= 1:
            d1 = torch.stack([torch.zeros_like(tau), one, 2 * tau, 3 * tau * tau], 1) * ns
            out.append(torch.einsum('np,npj,njc->nc', d1, Ms, Pl))
        if order >= 2:
            d2 = torch.stack([torch.zeros_like(tau), torch.zeros_like(tau), 2 * one, 6 * tau], 1) * (ns * ns)
            out.append(torch.einsum('np,npj,njc->nc', d2, Ms, Pl))
        return out


def _unit2(v):
    return v / torch.sqrt((v * v).sum(-1, keepdim=True)).clamp_min(1e-30)


def _spline_block(P, q, closed, per_span=8):
    K = P.shape[1]
    sb = _SplineBasis.get(K, per_span)
    with torch.no_grad():
        Pd, qd = P.detach(), q.detach()
        Cs = torch.einsum('tk,nkc->ntc', sb.Bs.to(P.dtype), Pd)
        t = sb.ts.to(P.dtype)[((Cs - qd[:, None, :]) ** 2).sum(-1).argmin(1)]
        del Cs
        def polish(t):
            for _ in range(8):
                C, C1, C2 = sb.curve(Pd, t, 2)
                r = C - qd
                g = (r * C1).sum(-1)
                hg = (C1 * C1).sum(-1)
                h = hg + (r * C2).sum(-1)
                # Newton where the full second derivative is safely positive, Gauss-Newton elsewhere
                # (unevenly spaced control points make the parameter speed vary strongly along a span)
                h = torch.where(h > 0.3 * hg, h, hg).clamp_min(1e-12)
                t = (t - (g / h).clamp(-sb.dt, sb.dt)).clamp(0.0, 1.0)
            return t
        t = polish(t)
        if closed:
            # the seam of a closed curve is one point with two parameters: a search that stops
            # at one end is repeated from the other end
            stuck = (t <= 1e-9) | (t >= 1.0 - 1e-9)
            if bool(stuck.any()):
                t2 = polish(torch.where(t <= 1e-9, torch.ones_like(t), torch.zeros_like(t)))
                d1 = ((sb.curve(Pd, t, 0)[0] - qd) ** 2).sum(-1)
                d2 = ((sb.curve(Pd, t2, 0)[0] - qd) ** 2).sum(-1)
                t = torch.where(stuck & (d2 < d1), t2, t)
    C, C1 = sb.curve(P, t, 1)
    tan = _unit2(C1)
    if closed:
        ends = (t <= 1e-9) | (t >= 1.0 - 1e-9)
        if bool(ends.any()):
            z = torch.zeros_like(t)
            ta = _unit2(sb.curve(P, z, 1)[1]) + _unit2(sb.curve(P, z + 1.0, 1)[1])
            tan = torch.where(ends[:, None], _unit2(ta), tan)
    nrm = torch.stack([-tan[:, 1], tan[:, 0]], -1)                  # left of the direction of travel
    r = q - C
    side = (r * nrm).sum(-1)
    dist = torch.sqrt((r * r).sum(-1) + 1e-30)
    interior = (t > 1e-9) & (t < 1.0 - 1e-9)
    sd = torch.where(interior, side, torch.where(side > 0, dist, -dist))
    if not closed:
        best = dist
        for point, tangent, forward in ((P[:, 0], _unit2(P[:, 1] - P[:, 0]), -1.0), (P[:, -1], _unit2(P[:, -1] - P[:, -2]), 1.0)):
            along = ((q - point) * tangent).sum(-1) * forward
            foot = point + (along.clamp_min(0.0) * forward)[:, None] * tangent
            rr = q - foot
            rd = torch.sqrt((rr * rr).sum(-1) + 1e-30)
            perp = torch.stack([-tangent[:, 1], tangent[:, 0]], -1)
            rs = ((q - point) * perp).sum(-1)
            on_ray = along > 0
            ray_sd = torch.where(on_ray, rs, torch.where(rs > 0, rd, -rd))
            take = rd < best - 1e-12
            sd = torch.where(take, ray_sd, sd)
            best = torch.where(take, rd, best)
    return sd


def _spline_torch(val, a):
    """a: [u, v, a0, b0, a1, b1, ...] tensors of one shape. Returns the signed planar distance."""
    _, K, closed = val
    shape = a[0].shape
    dt = torch.float64 if a[0].dtype == torch.float64 else torch.float32
    q = torch.stack([a[0].reshape(-1), a[1].reshape(-1)], -1).to(dt)
    P = torch.stack([torch.stack([a[2 + 2 * i].reshape(-1), a[3 + 2 * i].reshape(-1)], -1) for i in range(K)], 1).to(dt)
    n = q.shape[0]
    block = max(20_000, int(SPLINE_BUDGET // ((K - 3) * 8 + 1)))
    if n <= block:
        out = _spline_block(P, q, closed)
    else:
        out = torch.cat([_spline_block(P[i:i + block], q[i:i + block], closed) for i in range(0, n, block)])
    return out.reshape(shape).to(a[0].dtype)


# Host-side shortcut: a Spline DF whose control points are constants is a fixed planar
# distance map. It is computed once on a fine grid (more accurately than the general
# evaluator) and then read by bilinear interpolation. The native block is unchanged.
_LUT: dict = {}
LUT_STEP = 0.00125
LUT_DIR = None                     # set to a folder to keep the tables between runs


def _lut_table(node):
    import hashlib
    _, K, closed = node.val
    cp = np.array([[node.args[2 + 2 * i].val, node.args[3 + 2 * i].val] for i in range(K)], float)
    margin = 0.20 if closed else 0.30
    lo = cp.min(0) - margin
    n = np.ceil((cp.max(0) + margin - lo) / LUT_STEP).astype(int) + 1
    key = hashlib.md5(repr((cp.round(9).tolist(), closed, LUT_STEP, margin)).encode()).hexdigest()
    file = None if LUT_DIR is None else Path(LUT_DIR) / (key + '.npy')
    if file is not None and file.exists():
        tab = torch.tensor(np.load(file), device=DEV)
    else:
        us = torch.tensor(lo[0] + LUT_STEP * np.arange(n[0]), dtype=torch.float64, device=DEV)
        vs = torch.tensor(lo[1] + LUT_STEP * np.arange(n[1]), dtype=torch.float64, device=DEV)
        P = torch.tensor(cp, dtype=torch.float64, device=DEV)[None]
        per = 24
        rows = max(1, int(30_000_000 // (((K - 3) * per + 1) * n[1])))
        out = []
        with torch.no_grad():
            for i in range(0, n[0], rows):
                gu, gv = torch.meshgrid(us[i:i + rows], vs, indexing='ij')
                q = torch.stack([gu.reshape(-1), gv.reshape(-1)], -1)
                out.append(_spline_block(P.expand(q.shape[0], -1, -1), q, closed, per).reshape(gu.shape).float())
        tab = torch.cat(out)
        if file is not None:
            file.parent.mkdir(parents=True, exist_ok=True)
            np.save(file, tab.cpu().numpy())
    return tab, float(lo[0]), float(lo[1]), int(n[0]), int(n[1])


def _spline_lut(node, u, v):
    if node.uid not in _LUT:
        _LUT[node.uid] = _lut_table(node)
    tab, u0, v0, nu, nv = _LUT[node.uid]
    uc = u.clamp(u0, u0 + LUT_STEP * (nu - 1))
    vc = v.clamp(v0, v0 + LUT_STEP * (nv - 1))
    fu, fv = (uc - u0) / LUT_STEP, (vc - v0) / LUT_STEP
    iu = fu.detach().floor().clamp(0, nu - 2).long()
    iv = fv.detach().floor().clamp(0, nv - 2).long()
    wu, wv = fu - iu, fv - iv
    flat = tab.reshape(-1)
    base = iu * nv + iv
    a00, a01, a10, a11 = flat[base], flat[base + 1], flat[base + nv], flat[base + nv + 1]
    val = (a00 * (1 - wv) + a01 * wv) * (1 - wu) + (a10 * (1 - wv) + a11 * wv) * wu
    out2 = (u - uc) ** 2 + (v - vc) ** 2            # outside the table: continue by the distance to it
    far = torch.sqrt(out2 + 1e-20)
    return torch.where(out2 > 0, val + torch.where(val >= 0, far, -far), val).to(u.dtype)



# --------------------------------------------------------------------------
# Guides: cubic B-spline functions of one scalar, native spline in nTop
# --------------------------------------------------------------------------
class Guide:
    """Clamped uniform cubic B-spline g(u) on [u0, u1] from control values.

    In nTop this is a Spline by Control Points whose control abscissae are
    the Greville abscissae, so the curve is the graph of g. The field is read
    with Curve Axis Distance and remapped to the parameter field.
    """
    _names: set = set()

    section = None

    def __init__(self, name, u0, u1, ctrl):
        assert name not in Guide._names, 'duplicate guide ' + name
        Guide._names.add(name)
        ctrl = [float(c) for c in ctrl]
        n = len(ctrl)
        assert n >= 4
        self.name, self.u0, self.u1, self.ctrl = name, float(u0), float(u1), ctrl
        self.knots = np.array([0.] * 4 + [i / (n - 3) for i in range(1, n - 3)] + [1.] * 4)
        self.greville = [self.u0 + (self.u1 - self.u0) * float(sum(self.knots[i + 1:i + 4])) / 3 for i in range(n)]
        t = self.u0 + (self.u1 - self.u0) * self.knots
        self.spline = BSpline(t, np.array(ctrl), 3)
        pp = PPoly.from_spline(self.spline)
        keep = np.diff(pp.x) > 1e-12
        self._breaks = torch.tensor(pp.x[:-1][keep], dtype=torch.float64, device=DEV)
        self._coef = torch.tensor(pp.c[:, keep], dtype=torch.float64, device=DEV)
        self.offset = float(math.ceil(max(0.0, -min(ctrl))) + 1.0)

    @classmethod
    def through(cls, name, us, vs, n=None, u0=None, u1=None):
        """Least-squares control values so the guide passes through (us, vs)."""
        us, vs = np.asarray(us, float), np.asarray(vs, float)
        u0 = float(us[0]) if u0 is None else u0
        u1 = float(us[-1]) if u1 is None else u1
        n = n or max(4, len(us))
        knots = np.array([0.] * 4 + [i / (n - 3) for i in range(1, n - 3)] + [1.] * 4)
        t = u0 + (u1 - u0) * knots
        A = BSpline.design_matrix(np.clip(us, u0, u1 - 1e-12), t, 3).toarray()
        # mild second-difference regularization keeps the control polygon fair
        D = np.diff(np.eye(n), 2, axis=0) * 1e-4
        ctrl = np.linalg.lstsq(np.vstack([A, D]), np.concatenate([vs, np.zeros(n - 2)]), rcond=None)[0]
        return cls(name, u0, u1, ctrl)

    def __call__(self, u):
        return F('guide', (clamp(u, self.u0, self.u1),), self)

    def value(self, u):
        return float(self.spline(min(max(u, self.u0), self.u1)))

    def torch_eval(self, u):
        ud = u.to(torch.float64)
        idx = torch.bucketize(ud, self._breaks[1:].contiguous(), right=True)
        dx = ud - self._breaks[idx]
        c = self._coef
        out = c[0][idx]
        for k in range(1, c.shape[0]):
            out = out * dx + c[k][idx]
        return out.to(u.dtype)


# --------------------------------------------------------------------------
# Native primitives (base frame only)
# --------------------------------------------------------------------------
def _prim(kind, label, *params):
    node = F('prim', (), (kind,) + tuple(params))
    if label:
        node.label = label
    return node


def _t3(p):
    return (float(p[0]), float(p[1]), float(p[2]))


def capsule(p, q, r, label=None):
    return _prim('capsule', label, _t3(p), _t3(q), float(r))


def cylinder(p, q, r, label=None):
    return _prim('cylinder', label, _t3(p), _t3(q), float(r))


def sphere(c, r, label=None):
    return _prim('sphere', label, _t3(c), float(r))


def box(lo, hi, label=None):
    lo, hi = _t3(lo), _t3(hi)
    return _prim('box', label, tuple(min(a, b) for a, b in zip(lo, hi)), tuple(max(a, b) for a, b in zip(lo, hi)))


def torus(c, axis, R, r, label=None):
    a = np.array(axis, float)
    a = a / np.linalg.norm(a)
    return _prim('torus', label, _t3(c), _t3(a), float(R), float(r))


def _prim_torch(val, x, y, z):
    kind = val[0]
    if kind == 'sphere':
        c, r = val[1], val[2]
        return torch.sqrt((x - c[0]) ** 2 + (y - c[1]) ** 2 + (z - c[2]) ** 2) - r
    if kind in ('capsule', 'cylinder'):
        p, q, r = val[1], val[2], val[3]
        d = [q[i] - p[i] for i in range(3)]
        L2 = sum(v * v for v in d)
        L = math.sqrt(L2)
        ax, ay, az = x - p[0], y - p[1], z - p[2]
        tt = (ax * d[0] + ay * d[1] + az * d[2]) / L2
        if kind == 'capsule':
            tc = tt.clamp(0, 1)
            return torch.sqrt((ax - tc * d[0]) ** 2 + (ay - tc * d[1]) ** 2 + (az - tc * d[2]) ** 2) - r
        rad = torch.sqrt(((ax - tt * d[0]) ** 2 + (ay - tt * d[1]) ** 2 + (az - tt * d[2]) ** 2).clamp_min(0) + 1e-18)
        dr = rad - r
        da = (tt - 0.5).abs() * L - 0.5 * L
        outside = torch.sqrt(dr.clamp_min(0) ** 2 + da.clamp_min(0) ** 2 + 1e-18)
        return outside + torch.minimum(torch.maximum(dr, da), torch.zeros_like(dr))
    if kind == 'box':
        lo, hi = val[1], val[2]
        qx = (x - 0.5 * (lo[0] + hi[0])).abs() - 0.5 * (hi[0] - lo[0])
        qy = (y - 0.5 * (lo[1] + hi[1])).abs() - 0.5 * (hi[1] - lo[1])
        qz = (z - 0.5 * (lo[2] + hi[2])).abs() - 0.5 * (hi[2] - lo[2])
        outside = torch.sqrt(qx.clamp_min(0) ** 2 + qy.clamp_min(0) ** 2 + qz.clamp_min(0) ** 2)
        return outside + torch.maximum(qx, torch.maximum(qy, qz)).clamp_max(0)
    if kind == 'torus':
        c, a, R, r = val[1], val[2], val[3], val[4]
        px, py, pz = x - c[0], y - c[1], z - c[2]
        h = px * a[0] + py * a[1] + pz * a[2]
        rad = torch.sqrt(((px - h * a[0]) ** 2 + (py - h * a[1]) ** 2 + (pz - h * a[2]) ** 2).clamp_min(0))
        return torch.sqrt((rad - R) ** 2 + h * h) - r
    raise ValueError(kind)


# --------------------------------------------------------------------------
# Torch evaluation
# --------------------------------------------------------------------------
def _topo(roots):
    order, seen, stack = [], set(), [(r, False) for r in roots]
    while stack:
        node, done = stack.pop()
        if done:
            order.append(node)
            continue
        if node.uid in seen:
            continue
        seen.add(node.uid)
        stack.append((node, True))
        for a in node.args:
            if a.uid not in seen:
                stack.append((a, False))
    return order


def evaluate(roots, x, y, z):
    """Evaluate field nodes at coordinate tensors. Returns a list of tensors."""
    single = isinstance(roots, F)
    roots = [roots] if single else list(roots)
    order = _topo(roots)
    uses = {}
    for n in order:
        for a in n.args:
            uses[a.uid] = uses.get(a.uid, 0) + 1
    for r in roots:
        uses[r.uid] = uses.get(r.uid, 0) + 1
    memo = {}
    for n in order:
        op = n.op
        a = [memo[c.uid] for c in n.args]
        if op == 'const':
            v = torch.full_like(x, n.val)
        elif op == 'param':
            v = torch.full_like(x, n.val[1])
        elif op == 'x':
            v = x
        elif op == 'y':
            v = y
        elif op == 'z':
            v = z
        elif op == 'add':
            v = a[0] + a[1]
        elif op == 'sub':
            v = a[0] - a[1]
        elif op == 'mul':
            v = a[0] * a[1]
        elif op == 'div':
            v = a[0] / a[1]
        elif op == 'abs':
            v = a[0].abs()
        elif op == 'sqrt':
            v = torch.sqrt(a[0].clamp_min(0) + 1e-18)
        elif op == 'sin':
            v = torch.sin(a[0])
        elif op == 'cos':
            v = torch.cos(a[0])
        elif op == 'tan':
            v = torch.tan(a[0])
        elif op == 'exp':
            v = torch.exp(a[0])
        elif op == 'atan2':
            v = torch.atan2(a[0], a[1])
        elif op == 'pow':
            v = torch.pow(a[0].clamp_min(1e-9), a[1])
        elif op == 'min':
            v = a[0]
            for t in a[1:]:
                v = torch.minimum(v, t)
        elif op == 'max':
            v = a[0]
            for t in a[1:]:
                v = torch.maximum(v, t)
        elif op == 'clamp':
            v = torch.minimum(torch.maximum(a[0], a[1]), a[2])
        elif op == 'mix':
            v = a[0] + (a[1] - a[0]) * a[2]
        elif op == 'guide':
            v = n.val.torch_eval(a[0])
        elif op == 'prim':
            v = _prim_torch(n.val, x, y, z)
        elif op == 'spline':
            if all(c.op == 'const' for c in n.args[2:]):
                v = _spline_lut(n, a[0], a[1])
            else:
                v = _spline_torch(n.val, a)
        else:
            raise ValueError(op)
        memo[n.uid] = v
        for c in n.args:
            uses[c.uid] -= 1
            if uses[c.uid] == 0:
                memo.pop(c.uid, None)
    out = [memo[r.uid] for r in roots]
    return out[0] if single else out


def node_count(roots):
    roots = [roots] if isinstance(roots, F) else list(roots)
    return len(_topo(roots))


def probe(field, points):
    """Field values at an (N,3) array of points, float64 on CPU."""
    p = torch.tensor(np.asarray(points, float), dtype=torch.float64, device=DEV)
    with torch.no_grad():
        return evaluate(field, p[:, 0], p[:, 1], p[:, 2]).cpu().numpy()


def _grid_values(field, lo, hi, h, slab_cells=None, coarse=4, lip=1.6):
    """Field values on the grid. Large grids are evaluated in a narrow band around the surface:
    a first pass at the centres of blocks of coarse^3 cells finds the blocks the surface can
    reach (the field changes by at most `lip` per unit distance), the nodes of those blocks get
    exact values, all other nodes keep the value of their block centre (right sign, no crossing)."""
    slab_cells = slab_cells or SLAB_CELLS
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    n = np.maximum(np.ceil((hi - lo) / h).astype(int) + 1, 2)
    f32 = dict(dtype=torch.float32, device=DEV)

    def axes(start, step, counts):
        return [torch.tensor(start[k] + step * np.arange(counts[k]), **f32) for k in range(3)]

    def dense(ax):
        out = torch.empty(tuple(len(a) for a in ax), **f32)
        step = max(1, int(slab_cells // (len(ax[1]) * len(ax[2]))))
        for i in range(0, len(ax[0]), step):
            gx, gy, gz = torch.meshgrid(ax[0][i:i + step], ax[1], ax[2], indexing='ij')
            out[i:i + step] = evaluate(field, gx, gy, gz)
        return out

    with torch.no_grad():
        if int(n.prod()) < 2_000_000 or coarse <= 1:
            return dense(axes(lo, h, n)).cpu().numpy(), lo, n
        nb = np.ceil((n - 1) / coarse).astype(int)
        c = h * coarse
        cv = dense(axes(lo + 0.5 * c, c, nb))
        active = cv.abs() < lip * 0.866 * c + h
        idx = [torch.arange(n[k], device=DEV).div(coarse, rounding_mode='floor').clamp(max=nb[k] - 1) for k in range(3)]
        prev = [(torch.arange(n[k], device=DEV) - 1).clamp(min=0).div(coarse, rounding_mode='floor').clamp(max=nb[k] - 1) for k in range(3)]
        vol = cv[idx[0]][:, idx[1]][:, :, idx[2]].contiguous()
        mask = torch.zeros(tuple(n), dtype=torch.bool, device=DEV)
        for a in (idx[0], prev[0]):
            for b in (idx[1], prev[1]):
                for d in (idx[2], prev[2]):
                    mask |= active[a][:, b][:, :, d]
        pts = mask.nonzero()
        del mask
        for i in range(0, len(pts), slab_cells):
            q = pts[i:i + slab_cells]
            x = (lo[0] + h * q[:, 0]).float()
            y = (lo[1] + h * q[:, 1]).float()
            z = (lo[2] + h * q[:, 2]).float()
            vol[q[:, 0], q[:, 1], q[:, 2]] = evaluate(field, x, y, z)
        return vol.cpu().numpy(), lo, n


def gradient(field, pts, batch=None):
    """Field value and gradient at points (numpy in, numpy out)."""
    batch = batch or GRAD_BATCH
    vals, grads = [], []
    for i in range(0, len(pts), batch):
        p = torch.tensor(pts[i:i + batch], dtype=torch.float32, device=DEV, requires_grad=True)
        f = evaluate(field, p[:, 0], p[:, 1], p[:, 2])
        g, = torch.autograd.grad(f.sum(), p)
        vals.append(f.detach().cpu().numpy())
        grads.append(g.cpu().numpy())
    return np.concatenate(vals), np.concatenate(grads)


def _relax(field, v, f, h, iters=3, lam=0.55, pinned=None, y0=0.0):
    """Straighten the stair-stepped mesh along sharp edges: average each vertex with its neighbours,
    then put it back on the surface. Smooth regions are unaffected (the move there is tangential)."""
    from scipy import sparse
    n = len(v)
    i = np.concatenate([f[:, 0], f[:, 1], f[:, 2], f[:, 1], f[:, 2], f[:, 0]])
    j = np.concatenate([f[:, 1], f[:, 2], f[:, 0], f[:, 0], f[:, 1], f[:, 2]])
    A = sparse.csr_matrix((np.ones(len(i), np.float32), (i, j)), shape=(n, n))
    A.data[:] = 1.0
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1.0)[:, None]
    for _ in range(iters):
        v = (v + lam * ((A @ v) / deg - v)).astype(np.float32)
        for _ in range(2):
            if pinned is not None:
                v[pinned, 1] = y0
            val, g = gradient(field, v)
            if pinned is not None:
                g[pinned, 1] = 0.0
            g2 = np.maximum((g * g).sum(1), 1e-12)
            stepv = (val / g2)[:, None] * g
            norm = np.linalg.norm(stepv, axis=1)
            stepv *= np.minimum(1.0, (0.75 * h) / np.maximum(norm, 1e-12))[:, None]
            v = (v - stepv).astype(np.float32)
    return v


def mesh_field(field, lo, hi, h, refine=2, relax=3, pin_y0=False):
    """Marching cubes on a GPU-evaluated grid, then Newton projection and an edge clean-up pass.
    pin_y0: the box starts at the symmetry plane (lo[1]) and the surface is left open there; vertices on that
    plane stay on it, so the mesh can be mirrored and welded into a closed whole body."""
    from skimage import measure
    vol, lo, n = _grid_values(field, lo, hi, h)
    if not (vol.min() < 0 < vol.max()):
        return np.zeros((0, 3), np.float32), np.zeros((0, 3), np.int32), np.zeros((0, 3), np.float32)
    v, f, _, _ = measure.marching_cubes(vol, 0.0, spacing=(h, h, h))
    del vol
    v = (v + lo).astype(np.float32)
    pinned = (np.abs(v[:, 1] - lo[1]) < 1e-6 * max(h, 1e-3)) if pin_y0 else None
    for _ in range(refine):
        val, g = gradient(field, v)
        if pinned is not None:
            g[pinned, 1] = 0.0
        g2 = np.maximum((g * g).sum(1), 1e-12)
        stepv = (val / g2)[:, None] * g
        norm = np.linalg.norm(stepv, axis=1)
        stepv *= np.minimum(1.0, (0.75 * h) / np.maximum(norm, 1e-12))[:, None]
        v = (v - stepv).astype(np.float32)
    if relax and len(f):
        v = _relax(field, v, f, h, relax, pinned=pinned, y0=float(lo[1]))
    if pinned is not None:
        v[pinned, 1] = lo[1]
    _, g = gradient(field, v)
    nrm = g / np.maximum(np.linalg.norm(g, axis=1), 1e-12)[:, None]
    # orient faces along the outward gradient
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    flip = (fn * nrm[f[:, 0]]).sum(1) < 0
    f = f.copy()
    f[flip] = f[flip][:, ::-1]
    return v, f.astype(np.int32), nrm.astype(np.float32)


# --------------------------------------------------------------------------
# nTop recipe emission
# --------------------------------------------------------------------------
FUNC = {
    'add': 'add<real_field,real_field>', 'sub': 'subtract<real_field,real_field>',
    'mul': 'multiply<real_field,real_field>', 'div': 'divide<real_field,real_field>',
    'abs': 'abs<real_field>', 'sqrt': 'sqrt<real_field>', 'sin': 'sin<real_field>',
    'cos': 'cos<real_field>', 'tan': 'tan<real_field>', 'exp': 'exp<real_field>', 'atan2': 'atan2<real_field,real_field>',
    'pow': 'pow<real_field,real_field>', 'clamp': 'clamp<real_field,real_field,real_field>',
    'mix': 'mix<real_field,real_field,real_field>',
}
OPNAME = {'add': 'Add', 'sub': 'Subtract', 'mul': 'Multiply', 'div': 'Divide', 'abs': 'Abs', 'sqrt': 'Sqrt',
          'sin': 'Sin', 'cos': 'Cos', 'tan': 'Tan', 'exp': 'Exp', 'atan2': 'Atan2', 'pow': 'Pow', 'clamp': 'Clamp', 'mix': 'Mix',
          'min': 'Min', 'max': 'Max', 'guide': 'Guide', 'prim': 'Primitive', 'spline': 'Spline DF'}


FUNC_REAL = {
    'add': 'add<real,real>', 'sub': 'subtract<real,real>', 'mul': 'multiply<real,real>', 'div': 'divide<real,real>',
    'abs': 'abs<real>', 'sqrt': 'sqrt<real>', 'sin': 'sin<real>', 'cos': 'cos<real>', 'tan': 'tan<real>',
    'pow': 'pow<real,real>', 'clamp': 'clamp<real,real,real>', 'mix': 'mix<real,real,real>', 'atan2': 'atan2<real,real>',
}
_NUM = {
    'add': lambda a: a[0] + a[1], 'sub': lambda a: a[0] - a[1], 'mul': lambda a: a[0] * a[1], 'div': lambda a: a[0] / a[1],
    'abs': lambda a: abs(a[0]), 'sqrt': lambda a: math.sqrt(max(a[0], 0.0)), 'sin': lambda a: math.sin(a[0]),
    'cos': lambda a: math.cos(a[0]), 'tan': lambda a: math.tan(a[0]), 'exp': lambda a: math.exp(a[0]),
    'pow': lambda a: max(a[0], 1e-9) ** a[1], 'clamp': lambda a: min(max(a[0], a[1]), a[2]),
    'mix': lambda a: a[0] + (a[1] - a[0]) * a[2], 'atan2': lambda a: math.atan2(a[0], a[1]), 'min': min, 'max': max,
}


def is_scalar(f):
    """True when the node depends only on inputs and constants (no coordinate, guide, section or primitive)."""
    return all(n.op in _NUM or n.op in ('const', 'param') for n in _topo([lift(f)]))


def num(f):
    """Numeric value of a scalar node (inputs at their current values)."""
    memo = {}
    for n in _topo([lift(f)]):
        if n.op == 'const':
            memo[n.uid] = n.val
        elif n.op == 'param':
            memo[n.uid] = n.val[1]
        else:
            memo[n.uid] = _NUM[n.op]([memo[a.uid] for a in n.args])
    return float(memo[lift(f).uid])


class Recipe:
    """Collects named parts and writes one complete nTop recipe."""

    def __init__(self, title, description, prefix=''):
        self.title, self.description, self.prefix = title, description, prefix
        self.parts = []  # dicts: name, field, color, section, lo, hi
        self.checks = []  # (name, field, point)
        self._n = 0

    def part(self, name, field, color, section, lo, hi):
        self.parts.append(dict(name=name, field=lift(field), color=list(color), section=section,
                               lo=[float(v) for v in lo], hi=[float(v) for v in hi]))

    def check(self, name, field, point):
        self.checks.append((name, lift(field), [float(v) for v in point]))

    # -- literal helpers (formats recorded from build 42926 recipes)
    def _id(self):
        self._n += 1
        return f'{self.prefix}n{self._n:07d}'

    @staticmethod
    def real(v, units=None):
        return {'type': 'real', 'value': {'val': float(v), 'isFinite': True, 'units': units or {}}}

    @classmethod
    def length(cls, v):
        return cls.real(v, {'length': 1})

    @staticmethod
    def point(p):
        return {'type': 'point', 'value': [{'val': float(v), 'isFinite': True} for v in p]}

    @staticmethod
    def vec(p):
        return {'type': 'vector', 'value': {'units': {}, 'value': [{'val': float(v), 'isFinite': True} for v in p]}}

    def call(self, func, typ, *inputs):
        return {'func': func, 'type': typ, 'inputs': list(inputs), 'id': self._id(), 'name': func.split('<')[0]}

    def seq(self, typ, vals):
        return self.call('core.list<' + typ + '>', 'list<' + typ + '>', *vals)

    # -- emission
    def emit(self, max_depth=22, min_shared=4, names=None):
        body, sections = [], {}
        names = set() if names is None else names

        def var(name, typ, contents, section):
            base, k = name, 2
            while name in names:
                name = f'{base} ({k})'
                k += 1
            names.add(name)
            item = {'name': name, 'id': self._id(), 'type': typ, 'contents': contents, 'variable': True}
            body.append(item)
            sections[name] = section
            return {'ref': {'id': item['id']}, 'props': []}

        def prop(ref, p):
            return {'ref': ref['ref'], 'props': [p]}

        base = '00 Coordinates'
        coord = {}
        for i, ax in enumerate('XYZ'):
            plane = var(ax + ' reference plane', 'plane',
                        self.call('plane_from_normal<point,vector>[1.1.0]', 'plane', self.point([0, 0, 0]),
                                  self.vec([int(j == i) for j in range(3)])), base)
            coord[ax.lower()] = var(ax + ' coordinate [m]', 'real_field',
                                    self.call('divide<real_field,real_field>', 'real_field', prop(plane, 'scalar field'),
                                              self.length(1)), base)
        axis_ref = []

        def guide_axis():
            if not axis_ref:
                axis_ref.append(var('Guide axis', 'axis',
                                    self.call('axis<point,vector>', 'axis', self.point([0, 0, 0]), self.vec([1, 0, 0])), base))
            return axis_ref[0]

        roots = [p['field'] for p in self.parts] + [c[1] for c in self.checks]
        order = _topo(roots)
        uses = {}
        for n in order:
            for a in n.args:
                uses[a.uid] = uses.get(a.uid, 0) + 1
        # inline depth of each node; deep single-use chains are promoted to variables
        depth = {}
        size = {}
        promote = set()
        for n in order:
            leaf = n.op in ('const', 'x', 'y', 'z', 'param')
            d = 1 + max([0 if (a.uid in promote or a.op in ('const', 'x', 'y', 'z', 'param')) else depth[a.uid] for a in n.args], default=0)
            sz = (3 if n.op == 'guide' else 1) + sum(0 if (a.uid in promote or a.op in ('const', 'x', 'y', 'z', 'param')) else size[a.uid] for a in n.args)
            if leaf:
                d, sz = 0, 0
            elif n.label or n.op in ('prim', 'spline') or d > max_depth or (uses.get(n.uid, 0) > 1 and sz >= min_shared):
                promote.add(n.uid)
            depth[n.uid] = d
            size[n.uid] = sz
        refs, guide_fields, controls = {}, {}, {}
        auto = [0]
        owner = {}                                  # uid -> (label, section) of the nearest named user
        for p_ in self.parts:
            owner.setdefault(p_['field'].uid, (p_['field'].label or p_['name'], SECTION.get(p_['field'].uid, p_['section'])))
        for c_ in self.checks:
            owner.setdefault(c_[1].uid, (c_[1].label or c_[0], SECTION.get(c_[1].uid, '99 Checks')))
        for n in reversed(order):
            mine = owner.get(n.uid, ('Model', base))
            if n.label:
                mine = (n.label, SECTION.get(n.uid, mine[1]))
                owner[n.uid] = mine
            for a_ in n.args:
                owner.setdefault(a_.uid, mine)
        counter = {}
        scalar = {}
        for n in order:
            scalar[n.uid] = n.op in ('const', 'param') or (n.op in _NUM and all(scalar[a_.uid] for a_ in n.args))

        def helper_name(n):
            lab = owner[n.uid][0]
            counter[lab] = counter.get(lab, 0) + 1
            return f'{lab} | {OPNAME[n.op]} {counter[lab]}'

        def guide_field(g, section):
            section = g.section or section
            if g.name not in guide_fields:
                pts = var(g.name + ' control points', 'list<point>',
                          self.seq('point', [self.point([u, v + g.offset, 0]) for u, v in zip(g.greville, g.ctrl)]), section)
                spl = var(g.name + ' spline', 'spline',
                          self.call('spline_by_control_points<list<point>,integer>[5.20.0]', 'spline', pts,
                                    {'type': 'integer', 'value': {'val': 3}}), section)
                dist = self.call('curve_axis_distance<curve_interface,axis,vector>[5.30.0]', 'real_field', spl,
                                 guide_axis(), self.vec([0, 1, 0]))
                f = self.call('divide<real_field,real_field>', 'real_field',
                              self.call('subtract<real_field,real_field>', 'real_field', dist, self.length(g.offset)),
                              self.length(1))
                guide_fields[g.name] = var(g.name, 'real_field', f, section)
            return guide_fields[g.name]

        def prim_ref(val, label, section):
            kind = val[0]
            if kind == 'sphere':
                c = self.call('sphere<point,real>', 'sphere', self.point(val[1]), self.length(val[2]))
            elif kind == 'capsule':
                c = self.call('capsule<point,point,real>[5.26.0]', 'implicit', self.point(val[1]), self.point(val[2]), self.length(val[3]))
            elif kind == 'cylinder':
                c = self.call('cylinder<point,point,real>', 'cylinder', self.point(val[1]), self.point(val[2]), self.length(val[3]))
            elif kind == 'box':
                c = self.call('box_from_corners<point,point>', 'box', self.point(val[1]), self.point(val[2]))
            elif kind == 'torus':
                c = self.call('torus<point,vector,real,real>', 'torus', self.point(val[1]), self.vec(val[2]), self.length(val[3]), self.length(val[4]))
            else:
                raise ValueError(kind)
            typ = c['type']
            shape = var(label + ' primitive', typ, c, section)
            return self.call('divide<real_field,real_field>', 'real_field', prop(shape, 'scalar field'), self.length(1))

        def expr(n, section, part_name):
            if n.op == 'const':
                return self.real(n.val)
            if n.op in ('x', 'y', 'z'):
                return coord[n.op]
            if n.op == 'param':
                if n.val[0] not in controls:
                    controls[n.val[0]] = var(n.val[0], 'real', self.real(n.val[1]), PARAM_SECTION.get(n.val[0], '01 Inputs'))
                return controls[n.val[0]]
            if n.uid in refs:
                return refs[n.uid]
            section = owner[n.uid][1]
            if n.op == 'guide':
                g = n.val
                u = self.call('multiply<real_field,real_field>', 'real_field', expr(n.args[0], section, part_name), self.length(1))
                e = self.call('remap<real_field,real_field,real_field,real_field>', 'real_field', guide_field(g, section), u,
                              self.length(0), self.length(0))
            elif n.op == 'prim':
                auto[0] += 1
                e = prim_ref(n.val, n.label or f'{owner[n.uid][0]} {n.val[0]} {auto[0]}', section)
            elif n.op == 'spline':
                deg, K, _closed = n.val

                def as_len(a_):
                    if a_.op == 'const':
                        return self.length(a_.val)
                    return self.call('multiply<real_field,real_field>', 'real_field', expr(a_, section, part_name), self.length(1))

                def xy(a_, b_):
                    return self.call('vector_field_2d_from_components<real_field,real_field>[5.31.0]', 'vector_field_2d', as_len(a_), as_len(b_))
                cps = [xy(n.args[2 + 2 * i], n.args[3 + 2 * i]) for i in range(K)]
                auto[0] += 1
                sname = (n.label or f'{owner[n.uid][0]} | Section {auto[0]}') + ' Spline DF'
                sp = var(sname, 'implicit',
                         self.call('spline_implicit<list<vector_field_2d>,integer,vector_field_2d>[5.53.0]', 'implicit',
                                   self.seq('vector_field_2d', cps), {'type': 'integer', 'value': {'val': int(deg)}},
                                   xy(n.args[0], n.args[1])), section)
                e = self.call('divide<real_field,real_field>', 'real_field', sp, self.length(1))
            elif n.op in ('min', 'max'):
                ins = [expr(a, section, part_name) for a in n.args]
                kind = 'real' if scalar[n.uid] else 'real_field'
                if len(ins) == 2:
                    e = self.call(f'{n.op}<{kind},{kind}>', kind, *ins)
                else:
                    e = self.call(f'{n.op}<list<{kind}>>', kind, self.seq(kind, ins))
            elif scalar[n.uid]:
                e = self.call(FUNC_REAL[n.op], 'real', *[expr(a, section, part_name) for a in n.args])
            else:
                e = self.call(FUNC[n.op], 'real_field', *[expr(a, section, part_name) for a in n.args])
            if n.uid in promote:
                if n.label:
                    name = n.label
                else:
                    name = helper_name(n)
                if n.op == 'prim':
                    name = (n.label or name) + ' field'
                e = var(name, 'real' if scalar[n.uid] else 'real_field', e, section)
                refs[n.uid] = e
            return e

        def emit_tree(root, section, part_name):
            # emit promoted descendants first, in dependency order, to bound recursion
            for n in _topo([root]):
                if n.uid in promote and n.uid not in refs:
                    expr(n, section, part_name)
            return expr(root, section, part_name)

        final = {}
        for p in self.parts:
            f = emit_tree(p['field'], p['section'], p['name'])
            scaled = self.call('multiply<real_field,real_field>', 'real_field', f, self.length(1))
            bbox = self.call('create_bounding_box<point,point>', 'bounding_box', self.point(p['lo']), self.point(p['hi']))
            bodyf = self.call('set_bounding_box<implicit,bounding_box>', 'implicit', scaled, bbox)
            var(p['name'], 'implicit', bodyf, p['section'])
            final[p['name']] = p['color']
        check_names = {}
        for name, field, point in self.checks:
            f = emit_tree(field, '99 Checks', name)
            cname = 'CHECK ' + name
            var(cname, 'real', self.call('evaluate_field<real_field,point>', 'real', f, self.point(point)), '99 Checks')
            check_names[cname] = point
        doc = {'body': body, 'displayname': self.title, 'description': self.description,
               'name': 'user_func_' + str(uuid.uuid4()).replace('-', '_'), 'inputs': [], 'namespaces': [], 'version': [1, 0, 0]}
        order_sections = []
        for item in body:
            s = sections[item['name']]
            if s not in order_sections:
                order_sections.append(s)
        layout = {'sections': sorted(order_sections), 'variables': sections, 'final_bodies': final}
        funcs = set()

        def walk(v):
            if isinstance(v, dict):
                if 'func' in v:
                    funcs.add(v['func'])
                for w in v.values():
                    walk(w)
            elif isinstance(v, list):
                for w in v:
                    walk(w)
        walk(body)
        manifest = {'variables': len(body), 'functions': sorted(funcs), 'checks': check_names, 'controls': sorted(controls),
                    'parts': [p['name'] for p in self.parts], 'graph_nodes': len(order)}
        return doc, layout, manifest

    def write(self, folder, stem, names=None):
        from pathlib import Path
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        doc, layout, manifest = self.emit(names=names)
        (folder / f'{stem}.json').write_text(json.dumps(doc))
        (folder / f'{stem}_layout.json').write_text(json.dumps(layout, indent=1))
        (folder / f'{stem}_manifest.json').write_text(json.dumps(manifest, indent=1))
        return manifest


# --------------------------------------------------------------------------
# Native mesh export recipes (run headless with ntopcl convert)
# --------------------------------------------------------------------------
def export_recipe(name, field, lo, hi, stl_path, tolerance, folder, stem, sharpen=2):
    """Standalone recipe: one part's full closure, a mesh block and an STL export."""
    from pathlib import Path
    r = Recipe('Export | ' + name, 'Native mesh export of one model part.')
    r.part(name, field, [0.5, 0.5, 0.5, 1], '10 Part', lo, hi)
    doc, _, _ = r.emit()
    part = next(v for v in doc['body'] if v['name'] == name)
    mesh = {'func': 'mesh_from_implicit_body_2<implicit,real>', 'type': 'mesh', 'id': r._id(), 'name': 'mesh_from_implicit_body_2',
            'inputs': [{'ref': {'id': part['id']}, 'props': []}, r.length(tolerance)]}
    if sharpen:
        mesh = {'func': 'sharpen_mesh<mesh,implicit,integer,mesh_sharpen_enum>', 'type': 'mesh', 'id': r._id(), 'name': 'sharpen_mesh',
                'inputs': [mesh, {'ref': {'id': part['id']}, 'props': []}, {'type': 'integer', 'value': {'val': int(sharpen)}},
                           {'type': 'mesh_sharpen_enum', 'value': {'enum': 1}}]}
    doc['body'].append({'name': name + ' mesh export', 'id': r._id(), 'type': 'mesh_file_data',
                        'func': 'export_mesh<file_path,mesh,unit_length_enum>',
                        'inputs': [{'type': 'file_path', 'value': {'val': str(stl_path)}}, mesh,
                                   {'type': 'unit_length_enum', 'value': {'id': 'mm'}}]})
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f'{stem}.json'
    target.write_text(json.dumps(doc))
    return target


def read_stl(path):
    """Binary STL to welded (vertices in meters, faces)."""
    dt = np.dtype([('n', '<f4', (3,)), ('v', '<f4', (3, 3)), ('a', '<u2')])
    with open(path, 'rb') as stream:
        stream.seek(80)
        count = int.from_bytes(stream.read(4), 'little')
        tri = np.fromfile(stream, dtype=dt, count=count)['v'].copy()
    v, idx = np.unique(tri.reshape(-1, 3), axis=0, return_inverse=True)
    return v.astype(np.float64) * 0.001, idx.reshape(-1, 3).astype(np.int32)
