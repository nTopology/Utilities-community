"""Write the native nTop notebook: one recipe with every body, converted by the installed nTop (ntopcl).

  python tools/build_native.py [--stem fury] [--no-convert] [key=value ...]
Writes native/notebook/<stem>.json (recipe), <stem>_layout.json (sections, body colours), <stem>_manifest.json,
<stem>_checks.json (host values of the CHECK variables), then
  native/notebook/converted/<stem>.ntop   `ntopcl convert` of the recipe
  native/notebook/<stem>.ntop             the same notebook with sections, descriptions, collapsed blocks and colours
"""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
sys.path.insert(0, str(ROOT / 'tools'))
import fieldlab as fl
import registry, aircraft
from design import Design

args = sys.argv[1:]
stem = args[args.index('--stem') + 1] if '--stem' in args else 'fury'
over = {k: float(v) for k, v in (a.split('=') for a in args if '=' in a)}
NTOPCL = r'C:\Program Files\nTopology\nTopology\ntopcl.exe'
t0 = time.time()
ac = aircraft.build(Design(**over))
r = fl.Recipe('Fury | parametric Spline DF model',
              'Anduril YFQ-44A Fury class aircraft rebuilt as a parametric implicit model: Spline DF lofted outer mold line matched to public '
              'photographs, conventional or V tail, inlet duct, skin, frames, spars and ribs, engine envelope and fuel. '
              'Inputs are in ft, in and degrees; the model works in metres. X aft from the nose, Y to starboard, Z up.')
for p in ac.parts:
    r.part(p.name, p.field, list(registry.MAT[p.mat][0]) + [1.0], p.section, p.lo, p.hi)
m = ac.model
L = fl.num(m.L)
E = m.exterior
pts = {'Exterior above the crown': (0.5 * L, 0.0, 0.12 * L), 'Exterior inside the forebody': (0.2 * L, 0.0, 0.02 * L),
       'Exterior in the inlet mouth': (0.34 * L, 0.0, -0.02 * L), 'Exterior inside the wing': (0.6 * L, 0.2 * L, 0.006 * L),
       'Exterior at the fin': (0.93 * L, 0.0, 0.14 * L), 'Exterior ahead of the nose': (-0.05 * L, 0.0, 0.0)}
# two more points just behind the upper lip: the middle of the diverter slot (air) and the middle of the splitter plate
# under it (solid). Their heights are found on a vertical line through the model, so they follow the inputs.
import numpy as np
_x, _y = 0.30 * L, 12 * 0.0254
_z = np.arange(6.0, -12.0, -0.02) * 0.0254
_solid = np.asarray(fl.probe(E, [(_x, _y, float(z)) for z in _z])) < 0
_e = np.flatnonzero(np.diff(_solid.astype(int)))          # forebody | slot | plate | duct | cowl bottom
if len(_e) >= 3 and _solid[0]:
    pts['Exterior in the diverter slot'] = (_x, _y, round(float(0.5 * (_z[_e[0] + 1] + _z[_e[1]])), 4))
    pts['Exterior inside the splitter plate'] = (_x, _y, round(float(0.5 * (_z[_e[1] + 1] + _z[_e[2]])), 4))
host = {}
for name, pt in pts.items():
    r.check(name, E, pt)
    host['CHECK ' + name] = float(fl.probe(E, [pt])[0])
folder = ROOT / 'native' / 'notebook'
man = r.write(folder, stem)
(folder / f'{stem}_checks.json').write_text(json.dumps(dict(points=pts, host_values=host, inputs=m.d.values), indent=1))
print(f'{len(ac.parts)} bodies, {man.get("variables")} variables, {man.get("graph_nodes")} graph nodes, {time.time() - t0:.0f}s', flush=True)
print('host checks', {k: round(v, 5) for k, v in host.items()}, flush=True)
if '--no-convert' not in args:
    tmp = ROOT / '.local' / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    out = folder / 'converted'
    out.mkdir(exist_ok=True)
    part = out / f'{stem}.partial.ntop'
    part.unlink(missing_ok=True)
    env = dict(os.environ, TEMP=str(tmp), TMP=str(tmp))
    t = time.time()
    with (ROOT / '.local' / f'convert_{stem}.log').open('w') as log:
        code = subprocess.run([NTOPCL, 'convert', str(folder / f'{stem}.json'), str(part)], env=env, stdout=log, stderr=subprocess.STDOUT,
                              creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS).returncode
    print('ntopcl exit', code, 'seconds', round(time.time() - t), 'bytes', part.stat().st_size if part.exists() else None, flush=True)
    if part.exists() and part.stat().st_size > 10000:
        part.replace(out / f'{stem}.ntop')
        import organize_fury
        organize_fury.organize(stem)
