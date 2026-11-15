"""Mesh every body on the host and render views. render_parts.py <tag> [scale] [key=value ...] [--shots a b c] [--cut] [--plain] [--exterior]
--cut removes the port half of the skin and the fuel so the inside shows."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
import numpy as np
import fieldlab as fl
from design import Design
import aircraft, registry, preview

args = sys.argv[1:]
tag = args[0]
scale = float(args[1]) if len(args) > 1 and args[1].replace('.', '').isdigit() else 1.0
over = {k: float(v) for k, v in (a.split('=') for a in args if '=' in a and not a.startswith('--'))}
cut = '--cut' in args
exterior_only = '--exterior' in args            # only the skin and the boom: quick pictures of the outside
shots = args[args.index('--shots') + 1:] if '--shots' in args else (['cutaway', 'cut_side', 'cut_fwd', 'cut_aft', 'cut_under'] if cut else ['front34', 'rear34', 'top', 'side'])
shots = [s for s in shots if not s.startswith('--')]
ac = aircraft.build(Design(**over))
meshes = []
t = time.time()
for p in ac.parts:
    if p.name == 'Inlet duct air' or p.group == 'paint':
        continue
    if exterior_only and p.group != 'skin':
        continue
    col, rough, metal = registry.MAT[p.mat]
    if p.name == 'Skin':
        # the 3 mm shell is drawn as its outer surface: starboard half, mirrored unless this is a cutaway
        lo = [p.lo[0], 0.0, p.lo[2]]
        m = registry.surface_mesh(ac.model.exterior, lo, p.hi, p.h * scale, 'exterior')
        if not cut:
            v = m[0].copy()
            v[np.abs(v[:, 1]) < 2e-4, 1] = -3e-4          # the two halves overlap a hair, so no light shows through the seam
            m = (v, m[1], m[2])
            m = registry.join_meshes(m, registry.mirror_mesh(*m))
        meshes.append(dict(v=m[0], f=m[1], n=m[2], color=col, roughness=rough, metallic=metal))
        continue
    if cut and p.group == 'fuel':
        p = registry.Part(p.name + ' (starboard half)', fl.fmax(p.field, -fl.Y), p.mat, p.section, p.lo, p.hi, p.h, p.group)
    v, f, n = registry.mesh_part(p, scale)
    meshes.append(dict(v=v, f=f, n=n, color=col, roughness=rough, metallic=metal, opacity=0.6 if (cut and p.group == 'fuel') else 1.0))
print('meshed all in', round(time.time() - t), 's', flush=True)
livery = ac.model.livery
base = np.array(livery.BASE, np.float32)


def painter(pts):
    """Paint the pixels that lie on the outer mold line: paint colour over the base grey the skin was drawn in."""
    on_skin = np.abs(registry.values_at(ac.model.exterior, pts)) < 0.006
    return on_skin, livery.colour(pts[on_skin], registry) / base


plain = cut or '--plain' in args
for s in shots:
    preview.render(meshes, s, ROOT / 'preview' / tag / f'{s}.png', size=(1920, 1080), painter=None if plain else painter)
print('done')
