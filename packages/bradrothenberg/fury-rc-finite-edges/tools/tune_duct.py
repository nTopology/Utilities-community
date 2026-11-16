"""Find the duct floor heights that give a chosen area distribution from the throat to the engine face.

  python tools/tune_duct.py [throat/face area ratio, default 0.78]

The duct roof, the width ratio and the engine face are kept. At each station of the floor guide the floor is
moved until the duct area normal to the centreline equals the target: the throat area just behind the lower lip,
growing smoothly to the engine face area. Prints the floor values to paste into model/oml.py (FLOOR).
"""
import math, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
import fieldlab as fl
import registry, oml
from design import Design

ratio = float(sys.argv[1]) if len(sys.argv) > 1 else 0.78
L = oml.LREF
TS = [0.26, oml.T_LIP, 0.345, oml.T_ROOF_FREE, 0.43, 0.48, 0.54, 0.60, 0.66, 0.71, oml.T_FACE, 1.0]
FREE = [2, 3, 4, 5, 6, 7, 8, 9]                        # indices of TS that are tuned
vals = [oml.FLOOR.value(t * L) / L for t in TS]
a_face = math.pi * (oml.R_FACE * L) ** 2
t0, t1 = TS[FREE[0]], oml.T_FACE


def target(t):
    u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
    return a_face * (ratio + (1 - ratio) * (3 * u * u - 2 * u ** 3))


h = 0.004
y = np.arange(h / 2, 0.085 * L, h)
z = np.arange(-0.055 * L + h / 2, 0.085 * L, h)
Y, Z = np.meshgrid(y, z, indexing='ij')


def areas(values):
    fl.Guide._names.discard('Duct floor height') if isinstance(fl.Guide._names, set) else fl.Guide._names.pop('Duct floor height', None)
    oml.FLOOR = oml._g('Duct floor height', TS, values)
    af = oml.Airframe(Design())
    air = af.duct_air()
    out = []
    for i in FREE:
        res = []
        for dx in (-0.02, 0.0, 0.02):
            pts = np.c_[np.full(Y.size, TS[i] * L + dx), Y.ravel(), Z.ravel()]
            ins = (registry.values_at(air, pts) < 0).reshape(Y.shape)
            res.append((2 * ins.sum() * h * h, Z[ins].mean() if ins.any() else np.nan, 2 * (Y[ins].max() + h / 2) if ins.any() else 0.0))
        slope = (res[2][1] - res[0][1]) / 0.04
        out.append((res[1][0] / math.sqrt(1 + slope * slope), res[1][2]))
    return out


for it in range(10):
    a = areas(vals)
    err = [a[k][0] - target(TS[i]) for k, i in enumerate(FREE)]
    print(it, 'area in2', [round(v[0] / 0.0254 ** 2) for v in a], 'error in2', [round(e / 0.0254 ** 2) for e in err], flush=True)
    if max(abs(e) for e in err) < 0.0008:
        break
    for k, i in enumerate(FREE):
        vals[i] += 0.8 * err[k] / max(a[k][1] * 0.8, 0.2) / L
print('targets in2', [round(target(TS[i]) / 0.0254 ** 2) for i in FREE])
print('FLOOR stations', TS)
print('FLOOR values', [round(v, 4) for v in vals])
