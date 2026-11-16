"""Quick host look at the exterior: mesh the starboard half, mirror, render a set of views.

quick.py [tag] [h mm] [key=value ...]     e.g.  quick.py v1 14 tail_type=1
"""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
import numpy as np
import fieldlab as fl
from design import Design
from oml import Airframe
import preview
from registry import mirror_mesh, join_meshes

tag = sys.argv[1] if len(sys.argv) > 1 else 'quick'
h = float(sys.argv[2]) / 1000 if len(sys.argv) > 2 else 0.014
over = {k: float(v) for k, v in (a.split('=') for a in sys.argv[3:] if '=' in a)}
shots = [a for a in sys.argv[3:] if '=' not in a] or ['top', 'bottom', 'side', 'front', 'front34', 'rear34', 'under34', 'inlet']
af = Airframe(Design(**over))
lo, hi = af.box()
lo[1] = 0.0
t = time.time()
field = af.exterior()
print('nodes', fl.node_count([field]), 'device', fl.DEV, flush=True)
v, f, n = fl.mesh_field(field, lo, hi, h, pin_y0=True)
print(f'meshed {len(f)} tris in {time.time() - t:.0f}s  bbox {v.min(0).round(3)} {v.max(0).round(3)}', flush=True)
m = join_meshes((v, f, n), mirror_mesh(v, f, n))
(ROOT / '.local').mkdir(exist_ok=True)
np.savez(ROOT / '.local' / f'{tag}.npz', v=m[0], f=m[1], n=m[2], L=fl.num(af.L))
part = dict(v=m[0], f=m[1], n=m[2], color=(0.62, 0.64, 0.66), roughness=0.55)
for s in shots:
    preview.render([part], s, ROOT / 'preview' / tag / f'{s}.png', size=(1600, 900))
    preview.render([part], s, ROOT / 'preview' / tag / f'{s}_zebra.png', size=(1600, 900), zebra=True) if s in ('front34', 'rear34') else None
print('done', time.time() - t)
