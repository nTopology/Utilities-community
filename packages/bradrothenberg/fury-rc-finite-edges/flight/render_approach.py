"""Pictures of the landing approach: the gear-down aircraft placed at the attitude and position of the 6-DOF trace.

    python flight/render_approach.py mesh [scale]     mesh the aircraft with the gear down once and paint it (-> .local/approach_mesh.npz)
    python flight/render_approach.py stills           four stills along the approach (flight/out/approach_*.png)
    python flight/render_approach.py film             the last seconds to touchdown as an animated GIF (flight/out/approach.gif)

The trace is flight/sim/runs/approach/raw.npz (or trace_30hz.npz in the published package), flown in the Unlinked engine. The geometry is the notebook model with
gear_down = 1; it has no moving surfaces, so flaperons (30 deg down in the simulation) and stabilator are drawn neutral.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

FLIGHT = Path(__file__).resolve().parent
ROOT = FLIGHT.parent
OUT = FLIGHT / 'out'
MESH = ROOT / '.local' / 'approach_mesh.npz'
RUN = FLIGHT / 'sim' / 'runs' / 'approach'
FT, KT, DEG = 0.3048, 0.514444444, math.pi / 180.0


def build_mesh(scale=1.0):
    sys.path.insert(0, str(ROOT / 'model'))
    import fieldlab as fl          # noqa: F401
    from design import Design
    import aircraft, registry
    ac = aircraft.build(Design(gear_down=1.0))
    V, F, N, C = [], [], [], []
    n0 = 0
    livery = ac.model.livery
    for p in ac.parts:
        if p.name == 'Inlet duct air' or p.group == 'paint' or p.group not in ('skin', 'gear', 'fittings'):
            continue
        col = np.array(registry.MAT[p.mat][0][:3], np.float32)
        if p.name == 'Skin':
            lo, hi, hs = [p.lo[0], 0.0, p.lo[2]], list(p.hi), p.h * scale
            m = registry.surface_mesh(ac.model.exterior, lo, hi, hs, 'exterior')
            v = m[0].copy()
            v[np.abs(v[:, 1]) < 2e-4, 1] = -3e-4
            m = registry.join_meshes((v, m[1], m[2]), registry.mirror_mesh(v, m[1], m[2]))
            v, f, n = m
            rgb = livery.colour(v.astype(np.float32), registry).astype(np.float32)       # paint, markings and panel lines at the vertices
        else:
            v, f, n = registry.mesh_part(p, scale)
            rgb = np.tile(col, (len(v), 1))
        if len(f) == 0:
            continue
        V.append(v.astype(np.float32)); F.append(f.astype(np.int32) + n0); N.append(n.astype(np.float32)); C.append(rgb)
        n0 += len(v)
        print(p.name, len(v), flush=True)
    MESH.parent.mkdir(exist_ok=True)
    np.savez_compressed(MESH, v=np.concatenate(V), f=np.concatenate(F), n=np.concatenate(N), c=np.concatenate(C))
    print('wrote', MESH, n0, 'vertices')


def rot(e):
    e0, e1, e2, e3 = e
    return np.array([[e0 * e0 + e1 * e1 - e2 * e2 - e3 * e3, 2 * (e1 * e2 - e0 * e3), 2 * (e1 * e3 + e0 * e2)],
                     [2 * (e1 * e2 + e0 * e3), e0 * e0 - e1 * e1 + e2 * e2 - e3 * e3, 2 * (e2 * e3 - e0 * e1)],
                     [2 * (e1 * e3 - e0 * e2), 2 * (e2 * e3 + e0 * e1), e0 * e0 - e1 * e1 - e2 * e2 + e3 * e3]])


class Scene:
    """World frame of the pictures: x east, y north, z up, metres; origin at the touchdown point on the runway."""

    def __init__(self):
        import pyvista as pv
        self.pv = pv
        raw = RUN / 'raw.npz'
        z = np.load(raw if raw.exists() else RUN / 'trace_30hz.npz')
        self.info = json.loads((RUN / 'approach.json').read_text())
        par = json.loads((RUN / 'params.json').read_text())
        self.cg = np.array(par['physical']['cg_m'])
        self.t = z['t']
        self.d = {k: z[k] for k in ('pn', 'pe', 'height', 'e0', 'e1', 'e2', 'e3', 'tas', 'alpha', 'theta', 'phi', 'gear', 'flap', 'climb_rate', 'psi')}
        k = int(np.argmin(np.abs(z['t'] - self.info['touchdown']['at_s'])))
        self.k_td = k
        self.origin = np.array([z['pe'][k], z['pn'][k], 0.0])
        self.heading = float(z['psi'][k])                       # runway direction
        m = np.load(MESH)
        self.v, self.f, self.n, self.c = m['v'].astype(float), m['f'], m['n'].astype(float), m['c']
        # model frame (x aft, y starboard, z up) -> body axes (x forward, y right, z down) about the centre of gravity
        self.vb = np.c_[-(self.v[:, 0] - self.cg[0]), self.v[:, 1] - self.cg[1], -(self.v[:, 2] - self.cg[2])]
        self.nb = np.c_[-self.n[:, 0], self.n[:, 1], -self.n[:, 2]]
        self.faces = np.c_[np.full(len(self.f), 3), self.f].ravel()

    def index(self, t):
        return int(np.clip(np.searchsorted(self.t, t), 0, len(self.t) - 1))

    def aircraft(self, k):
        d = self.d
        R = rot([d[n][k] for n in ('e0', 'e1', 'e2', 'e3')])        # body -> north, east, down
        ned = self.vb @ R.T
        nn = self.nb @ R.T
        pos = np.array([d['pe'][k], d['pn'][k], d['height'][k]]) - self.origin
        w = np.c_[ned[:, 1], ned[:, 0], -ned[:, 2]] + pos
        mesh = self.pv.PolyData(w, self.faces)
        mesh.point_data['Normals'] = np.c_[nn[:, 1], nn[:, 0], -nn[:, 2]]
        mesh.point_data['rgb'] = (np.clip(self.c, 0, 1) * 255).astype(np.uint8)
        return mesh, pos

    def ground(self, pl):
        pv = self.pv
        along = np.array([math.sin(self.heading), math.cos(self.heading), 0.0])
        across = np.array([math.cos(self.heading), -math.sin(self.heading), 0.0])

        def quad(a0, a1, half, z, color, shift=0.0):
            c = [along * a0 + across * (shift - half), along * a1 + across * (shift - half), along * a1 + across * (shift + half), along * a0 + across * (shift + half)]
            pts = np.array(c) + [0, 0, z]
            pl.add_mesh(pv.PolyData(pts, [4, 0, 1, 2, 3]), color=color, lighting=False)

        quad(-9000, 9000, 9000, -0.05, '#6f7f5a')                 # field
        quad(-450, 2600, 23, 0.0, '#3b3d40')                      # runway 150 ft wide; touchdown 450 m (about 1,500 ft) past the threshold
        quad(-510, -450, 23, 0.005, '#2c2d2f')
        for s in np.arange(-410, 2560, 61.0):                     # centreline
            quad(s, s + 36.0, 0.45, 0.01, '#e9e9e4')
        for side in (-1, 1):
            quad(-450, 2600, 0.45, 0.01, '#e9e9e4', side * 22.0)  # edge lines
            for j in range(4):                                    # threshold bars
                quad(-445, -415, 0.9, 0.01, '#e9e9e4', side * (4.0 + 4.0 * j))
            quad(-150, -105, 3.0, 0.01, '#e9e9e4', side * 9.0)     # aiming point
        return along, across

    def picture(self, k, eye, target, path, fov=30, size=(1920, 1080), aa=True):
        pv = self.pv
        pl = pv.Plotter(off_screen=True, window_size=list(size), lighting='none')
        pl.set_background('#c9d9ea', top='#4f77a8')
        mesh, pos = self.aircraft(k)
        pl.add_mesh(mesh, scalars='rgb', rgb=True, smooth_shading=True, pbr=True, metallic=0.1, roughness=0.55, split_sharp_edges=False)
        self.ground(pl)
        for p_, inten in [((-10, -14, 30), 2.2), ((20, -12, 14), 1.2), ((6, 22, 12), 0.9), ((6, 0, -30), 0.9), ((-25, 4, 3), 0.6)]:
            light = pv.Light(position=tuple(pos + p_), focal_point=tuple(pos), intensity=inten, light_type='scene light')
            light.positional = False
            pl.add_light(light)
        pl.camera.position = tuple(eye)
        pl.camera.focal_point = tuple(target)
        pl.camera.up = (0, 0, 1)
        pl.camera.view_angle = fov
        pl.camera.clipping_range = (0.3, 30000)
        if aa:
            pl.enable_anti_aliasing('ssaa')
        img = pl.screenshot(None if path is None else str(path), return_img=True)
        pl.close()
        return img

    def caption(self, k):
        d = self.d
        hw = self.wheel_height(k)
        return (f"{d['tas'][k] / KT:.0f} kt   wheels {max(hw, 0) / FT:,.0f} ft above the runway   sink {-d['climb_rate'][k] / FT * 60:,.0f} ft/min   "
                f"angle of attack {d['alpha'][k] / DEG:.1f} deg   pitch {d['theta'][k] / DEG:+.1f} deg   bank {d['phi'][k] / DEG:+.0f} deg   gear {'down' if d['gear'][k] > 0.99 else 'in transit' if d['gear'][k] > 0.01 else 'up'}")

    def wheel_height(self, k):
        geo, d = self.info['wheel'], self.d
        th, ph = d['theta'][k], d['phi'][k]
        half = 67.5 * 0.0254 / 2
        down = lambda y: -geo['x'] * math.sin(th) + y * math.sin(ph) * math.cos(th) + geo['z'] * math.cos(ph) * math.cos(th)
        return d['height'][k] - max(down(half), down(-half))


def label(img, text, sub=None):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.fromarray(img[..., :3])
    dr = ImageDraw.Draw(im, 'RGBA')
    w, h = im.size
    try:
        f1 = ImageFont.truetype('arial.ttf', max(int(h * 0.026), 12)); f2 = ImageFont.truetype('arial.ttf', max(int(h * 0.02), 10))
    except OSError:
        f1 = f2 = ImageFont.load_default()
    band = int(h * (0.085 if sub else 0.055))
    dr.rectangle([0, h - band, w, h], fill=(11, 11, 11, 150))
    dr.text((int(w * 0.012), h - band + int(h * 0.01)), text, font=f1, fill=(255, 255, 255, 255))
    if sub:
        dr.text((int(w * 0.012), h - band + int(h * 0.046)), sub, font=f2, fill=(225, 225, 220, 255))
    return im


def stills():
    sc = Scene()
    along = np.array([math.sin(sc.heading), math.cos(sc.heading), 0.0])
    across = np.array([math.cos(sc.heading), -math.sin(sc.heading), 0.0])
    up = np.array([0, 0, 1.0])
    t_fl, t_td = sc.info['t_flare'], sc.t[sc.k_td]
    shots = [
        ('approach_1_base_turn', 16.0, lambda p: p - along * 5 + across * 16 + up * 5.0, 26, 'Base turn to final at 27 deg of bank, gear down'),
        ('approach_2_final', t_fl - 25.0, lambda p: p + along * 17 + across * 9 - up * 3.2, 24, 'On the 3 deg final at 110 kt, gear and flap down'),
        ('approach_3_threshold', t_fl - 1.0, lambda p: p + along * 13 - across * 13 - up * 1.5, 26, 'Short final, just before the flare'),
        ('approach_4_touchdown', t_td, lambda p: p + along * 3 - across * 21 + up * 0.2, 22, 'Main wheels on the runway'),
        ('approach_5_from_behind', t_fl - 12.0, lambda p: p - along * 30 + across * 2.5 + up * 4.5, 30, 'Final approach seen from behind: the runway ahead'),
    ]
    for name, t, eye, fov, text in shots:
        k = sc.index(t)
        _, pos = sc.aircraft(k)
        e = eye(pos)
        e[2] = max(e[2], 0.6)
        img = sc.picture(k, e, pos + up * 0.1, None, fov)
        label(img, text, sc.caption(k)).save(OUT / f'{name}.png')
        print(name, sc.caption(k), flush=True)


def film():
    from PIL import Image
    sc = Scene()
    along = np.array([math.sin(sc.heading), math.cos(sc.heading), 0.0])
    across = np.array([math.cos(sc.heading), -math.sin(sc.heading), 0.0])
    up = np.array([0, 0, 1.0])
    t_td = sc.t[sc.k_td]
    frames = []
    fps, t0 = 12, t_td - 14.0
    for t in np.arange(t0, t_td + 1e-6, 1.0 / fps):
        k = sc.index(t)
        _, pos = sc.aircraft(k)
        # the camera flies alongside, ahead and to the left, a little below at first and level with the wheels at the end
        s = (t - t0) / (t_td - t0)
        e = pos + along * (19 - 6 * s) - across * (13 + 5 * s) + up * (-2.5 + 3.0 * s)
        e[2] = max(e[2], 0.7)
        img = sc.picture(k, e, pos + up * 0.1, None, 26, size=(1280, 720), aa=True)
        im = label(img, 'Fury model: last 14 s to touchdown (6-DOF in Unlinked)', sc.caption(k)).resize((960, 540), Image.LANCZOS)
        frames.append(im.convert('P', palette=Image.ADAPTIVE, colors=128))
    frames += [frames[-1]] * fps
    frames[0].save(OUT / 'approach.gif', save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=False)
    print('wrote', OUT / 'approach.gif', len(frames), 'frames')


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if what == 'mesh':
        build_mesh(float(sys.argv[2]) if len(sys.argv) > 2 else 1.0)
    elif what == 'stills':
        stills()
    else:
        film()
