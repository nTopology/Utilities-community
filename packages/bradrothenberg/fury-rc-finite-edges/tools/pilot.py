"""Native pilot: nTop meshes one field from its own recipe (ntopcl convert), the host field is then
evaluated at the native mesh vertices. Small values mean nTop and the host compute the same shape.

pilot.py <what: exterior|wing|fuselage|tails> [tolerance mm] [key=value ...]
"""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
import numpy as np, torch
import fieldlab as fl
from design import Design
from oml import Airframe

what = sys.argv[1]
tol = float(sys.argv[2]) / 1000 if len(sys.argv) > 2 else 0.004
over = {k: float(v) for k, v in (a.split('=') for a in sys.argv[3:] if '=' in a)}
af = Airframe(Design(**over))
field = dict(exterior=af.exterior, wing=af.wing, fuselage=af.fuselage, tails=af.tails)[what]()
lo, hi = af.box()
tag = what + ''.join(f'_{k}{v:g}' for k, v in over.items())
out = ROOT / 'native' / 'pilot'
out.mkdir(parents=True, exist_ok=True)
tmp = ROOT / '.local' / 'tmp'
tmp.mkdir(parents=True, exist_ok=True)
stl = out / f'{tag}.stl'
stl.unlink(missing_ok=True)
recipe = fl.export_recipe('Pilot ' + what, field, lo, hi, stl, tol, out, tag)
doc = json.loads(recipe.read_text())
print('recipe variables', len(doc['body']), 'graph nodes', fl.node_count([field]), flush=True)
env = dict(os.environ, TEMP=str(tmp), TMP=str(tmp))
t = time.time()
with (ROOT / '.local' / f'pilot_{tag}.log').open('w') as log:
    code = subprocess.run([r'C:\Program Files\nTopology\nTopology\ntopcl.exe', 'convert', str(recipe), str(recipe.with_suffix('.ntop'))],
                          env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS).returncode
print('ntopcl exit', code, 'seconds', round(time.time() - t), 'stl', stl.exists(), flush=True)
if stl.exists():
    v, f = fl.read_stl(stl)
    q = torch.tensor(v, dtype=torch.float32, device=fl.DEV)
    val = np.abs(fl.evaluate(field, q[:, 0], q[:, 1], q[:, 2]).cpu().numpy().ravel())
    res = dict(what=tag, inputs=af.d.values, triangles=int(len(f)), tolerance_m=tol, host_abs_mean_m=float(val.mean()), host_abs_p99_m=float(np.quantile(val, 0.99)),
               host_abs_max_m=float(val.max()), bounds_min=v.min(0).round(4).tolist(), bounds_max=v.max(0).round(4).tolist(), seconds=round(time.time() - t))
    print(json.dumps(res), flush=True)
    (out / f'{tag}_verify.json').write_text(json.dumps(res, indent=1))
else:
    print(open(ROOT / '.local' / f'pilot_{tag}.log', errors='replace').read()[-1500:])
