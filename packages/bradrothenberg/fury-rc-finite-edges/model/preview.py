"""Fast offscreen previews of triangle meshes with pyvista (host render, not native)."""
from pathlib import Path
import numpy as np
import pyvista as pv

pv.OFF_SCREEN = True
C = (4.6, 0.0, 0.2)          # look-at centre of the airframe (9.1 m long, 6.8 m span)

SHOTS = {
    'front34': dict(eye=(-8.5, -8.0, 4.0), target=(4.2, 0, 0.2), fov=30),
    'rear34': dict(eye=(17.0, -8.5, 4.6), target=(5.2, 0, 0.3), fov=30),
    'low_front': dict(eye=(-6.5, -4.2, 0.2), target=(3.4, 0, 0.1), fov=30),
    'under34': dict(eye=(-7.0, -8.0, -5.0), target=(4.4, 0, 0.0), fov=30),
    'under_rear': dict(eye=(15.0, -7.0, -5.5), target=(5.0, 0, 0.0), fov=30),
    'top': dict(eye=(4.7, 0, 40.0), target=(4.7, 0, 0), fov=24, parallel=5.6, up=(0, 1, 0)),
    'plan': dict(eye=(5.1, 0, 40.0), target=(5.1, 0, 0), fov=24, parallel=7.1, up=(0, 1, 0)),
    'bottom': dict(eye=(4.7, 0, -40.0), target=(4.7, 0, 0), fov=24, parallel=5.6, up=(0, 1, 0)),
    'side': dict(eye=(4.7, -40.0, 0.5), target=(4.7, 0, 0.5), fov=24, parallel=5.6),
    'front': dict(eye=(-40.0, 0, 0.5), target=(0, 0, 0.5), fov=24, parallel=4.2),
    'rear': dict(eye=(50.0, 0, 0.5), target=(0, 0, 0.5), fov=24, parallel=4.2),
    'hero': dict(eye=(-4.2, -6.4, 3.0), target=(4.9, 0.2, 0.15), fov=30),
    'hero_rear': dict(eye=(13.6, -6.6, 3.4), target=(5.0, 0.2, 0.3), fov=30),
    'hero_low': dict(eye=(-3.6, -5.6, -1.6), target=(4.6, 0.0, 0.0), fov=30),
    'diverter': dict(eye=(0.9, -2.6, -0.55), target=(3.05, -0.25, -0.12), fov=24),
    'diverter_low': dict(eye=(0.3, -1.9, -1.0), target=(3.0, 0.0, -0.1), fov=24),
    'inlet': dict(eye=(-0.6, -2.3, -1.25), target=(3.2, 0, -0.15), fov=30),
    'inlet_front': dict(eye=(-3.5, -0.6, -0.9), target=(3.0, 0, -0.15), fov=22),
    'nozzle': dict(eye=(12.6, 2.2, 1.9), target=(8.8, 0, 0.35), fov=30),
    'nose': dict(eye=(-3.2, -3.4, 1.0), target=(1.4, 0, 0.1), fov=30),
    'cutaway': dict(eye=(-5.5, -8.5, 6.5), target=(4.6, 0.3, 0.0), fov=30),
    'cut_side': dict(eye=(4.7, -40.0, 0.4), target=(4.7, 0, 0.4), fov=24, parallel=5.4),
    'cut_fwd': dict(eye=(-1.5, -5.0, 3.2), target=(3.4, -0.3, 0.1), fov=30),
    'cut_aft': dict(eye=(11.5, -5.5, 3.6), target=(6.6, -0.6, 0.2), fov=30),
    'cut_under': dict(eye=(-2.5, -6.0, -4.0), target=(4.4, -0.3, -0.1), fov=30),
}


def polydata(v, f, n=None):
    faces = np.hstack([np.full((len(f), 1), 3, np.int64), f.astype(np.int64)]).ravel()
    m = pv.PolyData(np.asarray(v, np.float64), faces)
    if n is not None:
        m.point_data['Normals'] = np.asarray(n, np.float32)
        m.point_data.active_normals_name = 'Normals'
    return m


def pixel_points(pl, size):
    """World position of the surface seen in every pixel (rows from the top), and which pixels show a surface."""
    import vtk
    w, h = size
    f = vtk.vtkWindowToImageFilter()
    f.SetInput(pl.render_window)
    f.ReadFrontBufferOff()
    f.SetInputBufferTypeToZBuffer()
    f.Update()
    zb = np.asarray(pv.wrap(f.GetOutput()).active_scalars, np.float64).reshape(h, w)[::-1]
    m = pl.camera.GetCompositeProjectionTransformMatrix(w / h, -1, 1)
    inv = np.linalg.inv(np.array([[m.GetElement(i, j) for j in range(4)] for i in range(4)]))
    ys, xs = np.mgrid[0:h, 0:w]
    ndc = np.stack([(xs + 0.5) / w * 2 - 1, 1 - (ys + 0.5) / h * 2, zb * 2 - 1, np.ones_like(zb)], -1)
    pts = ndc @ inv.T
    return pts[..., :3] / pts[..., 3:], zb < 1 - 1e-7


def render(parts, shot, path, size=(1920, 1080), background=('#5d7fa6', '#b9cde3'), ssao=True, zebra=False, painter=None):
    """painter(points) -> (mask of the points it paints, rgb factor for those points): colours the picture per pixel
    (paint, markings, panel lines) at twice the size, then the picture is reduced."""
    out_size = size
    if painter:
        size = (size[0] * 2, size[1] * 2)
    """parts: iterable of dicts with v, f, optional n, color (rgb 0-1), optional metallic/roughness/opacity."""
    cam = SHOTS[shot] if isinstance(shot, str) else shot
    pl = pv.Plotter(off_screen=True, window_size=list(size), lighting='none')
    pl.set_background(background[0], top=background[1])
    for p in parts:
        if len(p['f']) == 0:
            continue
        mesh = polydata(p['v'], p['f'], p.get('n'))
        if p.get('n') is None:
            mesh = mesh.compute_normals(split_vertices=False, feature_angle=40)
        if zebra:
            nrm = np.asarray(mesh.point_data['Normals'])
            d = np.array(zebra if not isinstance(zebra, bool) else (0.35, 0.25, 0.9), float)
            d /= np.linalg.norm(d)
            mesh.point_data['zebra'] = (np.floor((nrm @ d) * 28) % 2).astype(np.float32)
            pl.add_mesh(mesh, scalars='zebra', cmap=['#101010', '#f2f2f2'], show_scalar_bar=False, smooth_shading=True,
                        interpolate_before_map=True)
            continue
        pl.add_mesh(mesh, color=p['color'][:3], smooth_shading=True, pbr=True, metallic=p.get('metallic', 0.0),
                    roughness=p.get('roughness', 0.5), split_sharp_edges=False, opacity=p.get('opacity', 1.0))
    for pos, inten in [((-10, -14, 30), 2.4), ((20, -12, 14), 1.3), ((6, 22, 12), 1.0), ((6, 0, -30), 1.1), ((-25, 4, 3), 0.7)]:
        light = pv.Light(position=pos, focal_point=C, intensity=inten, light_type='scene light')
        light.positional = False
        pl.add_light(light)
    pl.camera.position = cam['eye']
    pl.camera.focal_point = cam['target']
    pl.camera.up = cam.get('up', (0, 0, 1))
    pl.camera.view_angle = cam['fov']
    if 'parallel' in cam:
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = cam['parallel'] * size[1] / size[0]
    pl.camera.clipping_range = (0.2, 200)
    if ssao and not zebra and 'parallel' not in cam:      # ambient occlusion draws contour bands in parallel views
        try:
            pl.enable_ssao(radius=0.35, bias=0.01, kernel_size=128, blur=True)
        except Exception:
            pass
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not painter:
        pl.enable_anti_aliasing('ssaa')
        pl.screenshot(str(path))
        pl.close()
        return path
    from PIL import Image
    img = np.asarray(pl.screenshot(None, return_img=True), np.float32)[..., :3]
    pts, seen = pixel_points(pl, size)
    pl.close()
    idx = np.flatnonzero(seen.ravel())
    mask, factor = painter(pts.reshape(-1, 3)[idx].astype(np.float32))
    flat = img.reshape(-1, 3)
    flat[idx[mask]] = np.clip(flat[idx[mask]] * factor, 0, 255)
    Image.fromarray(flat.reshape(img.shape).astype(np.uint8)).resize(out_size, Image.LANCZOS).save(str(path))
    return path
