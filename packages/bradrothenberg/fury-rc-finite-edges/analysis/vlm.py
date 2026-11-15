"""Vortex-lattice estimate of lift-curve slope, neutral point and the tail's directional stability,
for the conventional tail and the V-tail.

  python analysis/vlm.py [key=value ...]     ->  analysis/results/vlm.json and vlm.md

Flat lifting surfaces from the planform inputs: the wing and the horizontal tail carried to the centreline,
the fin, or the two V-tail panels. Horseshoe vortices on the panel quarter-chord lines, control points on the
three-quarter-chord lines, trailing legs straight aft, Prandtl-Glauert stretching for Mach number.
No thickness, no camber, no fuselage volume: the fuselage adds a nose-up (destabilising) moment that this
method leaves out, so the real neutral point is further forward than the number here. Estimate.
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
from design import Design

FT, IN = 0.3048, 0.0254


def horseshoe(p, a, b):
    """Velocity at points p (n, 3) from unit horseshoe vortices with bound segments a -> b (m, 3) and legs to +x infinity."""
    def seg(p, a, b):
        r1, r2 = p[:, None, :] - a[None], p[:, None, :] - b[None]
        cr = np.cross(r1, r2)
        n1, n2 = np.linalg.norm(r1, axis=2), np.linalg.norm(r2, axis=2)
        den = n1 * n2 * (n1 * n2 + (r1 * r2).sum(2))
        return cr * ((n1 + n2) / np.where(np.abs(den) < 1e-14, np.inf, den))[..., None] / (4 * math.pi)

    def leg(p, a):
        r = p[:, None, :] - a[None]
        d2 = r[..., 1] ** 2 + r[..., 2] ** 2
        n = np.linalg.norm(r, axis=2)
        f = (1.0 + r[..., 0] / n) / np.where(d2 < 1e-14, np.inf, d2) / (4 * math.pi)
        w = np.zeros_like(r)
        w[..., 1] = -r[..., 2] * f
        w[..., 2] = r[..., 1] * f
        return w
    return seg(p, a, b) + leg(p, b) - leg(p, a)


def panel(root_le, tip_le, root_chord, tip_chord, mirror=True, nc=8, ns=24):
    """Lattice of one tapered panel from the root leading edge to the tip leading edge (and its mirror image)."""
    root_le, tip_le = np.array(root_le, float), np.array(tip_le, float)
    th = np.linspace(0.0, math.pi / 2, ns + 1)
    eta = np.sin(th)                                         # finer towards the tip
    le = root_le[None] + eta[:, None] * (tip_le - root_le)[None]
    ch = root_chord + eta * (tip_chord - root_chord)
    A, B, P = [], [], []
    for i in range(ns):
        for j in range(nc):
            f1, f2 = (j + 0.25) / nc, (j + 0.75) / nc
            a = le[i] + [f1 * ch[i], 0, 0]
            b = le[i + 1] + [f1 * ch[i + 1], 0, 0]
            c = 0.5 * (le[i] + le[i + 1]) + [f2 * 0.5 * (ch[i] + ch[i + 1]), 0, 0]
            A.append(a), B.append(b), P.append(c)
            if mirror:
                m = np.array([1.0, -1.0, 1.0])
                A.append(b * m), B.append(a * m), P.append(c * m)
    return np.array(A), np.array(B), np.array(P)


def surfaces(d, tail):
    """Panels of the configuration. tail: 'none', 'conventional' or 'vee'."""
    v = d.value
    L = v('length') * FT
    out = []
    b2 = v('wing_span') * FT / 2
    g = math.radians(v('wing_dihedral'))
    x0 = v('wing_apex') * 0.01 * L
    out.append(('wing', panel([x0, 0, v('wing_height') * IN], [x0 + b2 * math.tan(math.radians(v('wing_sweep'))), b2 * math.cos(g), v('wing_height') * IN + b2 * math.sin(g)],
                              v('wing_root_chord') * FT, v('wing_tip_chord') * FT)))
    if tail == 'conventional':
        h2 = v('htail_span') * FT / 2
        gh = math.radians(v('htail_dihedral'))
        xh = v('htail_apex') * 0.01 * L
        out.append(('horizontal tail', panel([xh, 0, v('htail_height') * IN], [xh + h2 * math.tan(math.radians(v('htail_sweep'))), h2 * math.cos(gh), v('htail_height') * IN + h2 * math.sin(gh)],
                                             v('htail_root_chord') * FT, v('htail_tip_chord') * FT)))
        hf = v('fin_height') * FT
        xf = v('fin_apex') * 0.01 * L
        out.append(('fin', panel([xf, 0, v('fin_root_height') * IN], [xf + hf * math.tan(math.radians(v('fin_sweep'))), 0, v('fin_root_height') * IN + hf],
                                 v('fin_root_chord') * FT, v('fin_tip_chord') * FT, mirror=False)))
    elif tail == 'vee':
        lv = v('vtail_length') * FT
        c = math.radians(v('vtail_cant'))
        xv = v('vtail_apex') * 0.01 * L
        out.append(('V-tail', panel([xv, 0, v('vtail_root_height') * IN], [xv + lv * math.tan(math.radians(v('vtail_sweep'))), lv * math.cos(c), v('vtail_root_height') * IN + lv * math.sin(c)],
                                    v('vtail_root_chord') * FT, v('vtail_tip_chord') * FT)))
    return out


def reference(d):
    v = d.value
    L = v('length') * FT
    b = v('wing_span') * FT
    cr, ct = v('wing_root_chord') * FT, v('wing_tip_chord') * FT
    lam = ct / cr
    S = 0.5 * (cr + ct) * b
    mac = 2 / 3 * cr * (1 + lam + lam * lam) / (1 + lam)
    ymac = b / 6 * (1 + 2 * lam) / (1 + lam)
    xle = v('wing_apex') * 0.01 * L + ymac * math.tan(math.radians(v('wing_sweep')))
    return dict(S=S, b=b, mac=mac, x_mac_le=xle, L=L)


def solve(d, tail, mach=0.0):
    ref = reference(d)
    beta = math.sqrt(1 - mach * mach)
    parts = surfaces(d, tail)
    A = np.vstack([p[1][0] for p in parts])
    B = np.vstack([p[1][1] for p in parts])
    P = np.vstack([p[1][2] for p in parts])
    owner = np.concatenate([[k] * len(p[1][0]) for k, p in enumerate(parts)])
    s = np.array([1 / beta, 1.0, 1.0])                       # Prandtl-Glauert: x stretched by 1 / beta
    As, Bs, Ps = A * s, B * s, P * s
    N = np.cross(np.array([1.0, 0, 0])[None], Bs - As)
    N /= np.linalg.norm(N, axis=1)[:, None]
    vel = horseshoe(Ps, As, Bs)
    M = np.einsum('ijk,ik->ij', vel, N)
    xref = np.array([ref['x_mac_le'] + 0.25 * ref['mac'], 0.0, 0.0])
    res = {}
    for name, dv in (('alpha', np.array([0.0, 0.0, 1.0])), ('beta', np.array([0.0, -1.0, 0.0]))):     # unit angle, unit speed
        gamma = np.linalg.solve(M, -(N @ dv))
        F = gamma[:, None] * np.cross(np.array([1.0, 0, 0])[None], Bs - As)       # rho = 1, V = 1
        mid = 0.5 * (A + B)
        mom = np.cross(mid - xref, F)
        q_s = 0.5 * ref['S']
        tot = dict(force=(F.sum(0) / q_s).tolist(), moment=mom.sum(0).tolist())
        by = {parts[k][0]: dict(force=(F[owner == k].sum(0) / q_s).tolist(), moment=mom[owner == k].sum(0).tolist()) for k in range(len(parts))}
        res[name] = dict(total=tot, parts=by)
    # with the stretching the forces on the stretched wing equal beta times the compressible ones per unit of physical alpha:
    # C(compressible) = C(stretched solution) / beta (Goethert rule for a thin surface)
    k = 1.0 / beta
    cla = res['alpha']['total']['force'][2] * k
    cma = res['alpha']['total']['moment'][1] / (0.5 * ref['S'] * ref['mac']) * k
    cyb = res['beta']['total']['force'][1] * k
    cnb = res['beta']['total']['moment'][2] / (0.5 * ref['S'] * ref['b']) * k
    clb = res['beta']['total']['moment'][0] / (0.5 * ref['S'] * ref['b']) * k
    x_np = xref[0] - cma / cla * ref['mac']
    return dict(tail=tail, mach=mach, cl_alpha_per_rad=cla, cl_alpha_per_deg=cla * math.pi / 180, cm_alpha_per_rad_about_quarter_mac=cma,
                neutral_point_station_m=x_np, neutral_point_percent_mac=(x_np - ref['x_mac_le']) / ref['mac'] * 100,
                cy_beta_per_rad=cyb, cn_beta_per_rad=cnb, cl_beta_per_rad=clb,
                lift_share={n: p['force'][2] / res['alpha']['total']['force'][2] for n, p in res['alpha']['parts'].items()}, panels=int(len(A)))


def main():
    over = {k: float(v) for k, v in (a.split('=') for a in sys.argv[1:] if '=' in a)}
    d = Design(**over)
    ref = reference(d)
    v = d.value
    L = ref['L']
    # tail volume coefficients (areas of the exposed input trapezoids carried to the centreline)
    sh = 0.5 * (v('htail_root_chord') + v('htail_tip_chord')) * FT * v('htail_span') * FT
    sf = 0.5 * (v('fin_root_chord') + v('fin_tip_chord')) * FT * v('fin_height') * FT
    sv = (v('vtail_root_chord') + v('vtail_tip_chord')) * FT * v('vtail_length') * FT
    c = math.radians(v('vtail_cant'))

    def arm(apex, root, tip, span_half, sweep):
        lam = tip / root
        mac = 2 / 3 * root * (1 + lam + lam * lam) / (1 + lam)
        ym = span_half / 3 * (1 + 2 * lam) / (1 + lam)
        return apex * 0.01 * L + ym * math.tan(math.radians(sweep)) + 0.25 * mac * FT - (ref['x_mac_le'] + 0.25 * ref['mac'])
    lh = arm(v('htail_apex'), v('htail_root_chord'), v('htail_tip_chord'), v('htail_span') * FT / 2, v('htail_sweep'))
    lf = arm(v('fin_apex'), v('fin_root_chord'), v('fin_tip_chord'), v('fin_height') * FT, v('fin_sweep'))
    lv = arm(v('vtail_apex'), v('vtail_root_chord'), v('vtail_tip_chord'), v('vtail_length') * FT, v('vtail_sweep'))
    geo = dict(reference_area_m2=ref['S'], span_m=ref['b'], mean_aerodynamic_chord_m=ref['mac'], mac_leading_edge_station_m=ref['x_mac_le'],
               horizontal_tail=dict(area_m2=sh, arm_m=lh, volume_coefficient=sh * lh / (ref['S'] * ref['mac'])),
               fin=dict(area_m2=sf, arm_m=lf, volume_coefficient=sf * lf / (ref['S'] * ref['b'])),
               v_tail=dict(area_m2=sv, arm_m=lv, horizontal_volume_coefficient=sv * math.cos(c) ** 2 * lv / (ref['S'] * ref['mac']),
                           vertical_volume_coefficient=sv * math.sin(c) ** 2 * lv / (ref['S'] * ref['b'])))
    runs = [solve(d, t, m) for m in (0.0, 0.6) for t in ('none', 'conventional', 'vee')]
    cg = None
    mf = ROOT / 'analysis' / 'results' / 'mass.json'
    if mf.exists() and not over:
        t = json.loads(mf.read_text())['totals']
        cg = dict(modelled_items_full_fuel_station_m=t['modelled_with_full_fuel_cg_m'][0], modelled_items_no_fuel_station_m=t['modelled_without_fuel_cg_m'][0])
    out = dict(inputs=d.values, method='flat-plate vortex lattice of the planform inputs (estimate; no fuselage, thickness or camber)', geometry=geo, results=runs, centre_of_gravity=cg)
    res = ROOT / 'analysis' / 'results'
    res.mkdir(parents=True, exist_ok=True)
    (res / 'vlm.json').write_text(json.dumps(out, indent=1))
    name = {'none': 'Wing alone', 'conventional': 'Conventional tail', 'vee': 'V-tail'}
    md = ['# Lift and stability by vortex lattice (estimate)', '',
          'Flat lifting surfaces from the planform inputs. No fuselage volume, thickness or camber: the fuselage moves the real neutral point forward',
          'and reduces the real directional stability, so read the numbers as a comparison of the two tails and a first estimate.', '',
          f"Reference: wing area {ref['S'] / FT ** 2:.1f} ft2, span {ref['b'] / FT:.2f} ft, mean aerodynamic chord {ref['mac'] / FT:.2f} ft, "
          f"its leading edge at station {ref['x_mac_le'] / FT:.2f} ft.", '',
          '| Tail | Area [ft2] | Arm [ft] | Volume coefficient |', '|---|---:|---:|---:|',
          f"| Horizontal tail (both sides) | {sh / FT ** 2:.1f} | {lh / FT:.1f} | {geo['horizontal_tail']['volume_coefficient']:.2f} |",
          f"| Fin | {sf / FT ** 2:.1f} | {lf / FT:.1f} | {geo['fin']['volume_coefficient']:.3f} |",
          f"| V-tail (both panels, cant {v('vtail_cant'):.0f} deg) | {sv / FT ** 2:.1f} | {lv / FT:.1f} | horizontal {geo['v_tail']['horizontal_volume_coefficient']:.2f}, vertical {geo['v_tail']['vertical_volume_coefficient']:.3f} |",
          '', '| Mach | Configuration | Lift slope [per deg] | Neutral point station [ft] | Neutral point [% MAC] | Cn beta of the lifting surfaces [per rad] | CY beta [per rad] |',
          '|---:|---|---:|---:|---:|---:|---:|']
    for r in runs:
        md.append(f"| {r['mach']:.1f} | {name[r['tail']]} | {r['cl_alpha_per_deg']:.4f} | {r['neutral_point_station_m'] / FT:.2f} | {r['neutral_point_percent_mac']:.0f} | "
                  f"{r['cn_beta_per_rad']:+.3f} | {r['cy_beta_per_rad']:+.3f} |")
    if cg:
        md += ['', 'Centre of gravity of the modelled items (structure, engine, landing gear, fuel; no systems or stores) from analysis/results/mass.md:',
               f"full fuel at station {cg['modelled_items_full_fuel_station_m'] / FT:.2f} ft, no fuel at station {cg['modelled_items_no_fuel_station_m'] / FT:.2f} ft."]
        for r in runs:
            if r['mach'] == 0.0 and r['tail'] != 'none':
                sm = [(r['neutral_point_station_m'] - cg[k]) / ref['mac'] * 100 for k in ('modelled_items_full_fuel_station_m', 'modelled_items_no_fuel_station_m')]
                md.append(f"- {name[r['tail']]}: lattice neutral point is {sm[0]:+.0f} % MAC aft of the full-fuel point and {sm[1]:+.0f} % MAC aft of the no-fuel point "
                          '(positive = stable, before the fuselage effect).')
    (res / 'vlm.md').write_text('\n'.join(md))
    print('\n'.join(md))


if __name__ == '__main__':
    main()
