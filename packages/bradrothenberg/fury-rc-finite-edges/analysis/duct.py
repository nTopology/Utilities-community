"""Inlet duct: area distribution, throat, engine face, line of sight and one-dimensional Mach numbers.

  python analysis/duct.py [key=value ...]     ->  analysis/results/duct.json, duct.md, duct.png

The duct air body of the model is cut by planes of constant station. The area of each cut is corrected to the
area normal to the duct centreline with the slope of the line through the centroids. The Mach numbers are
one-dimensional isentropic values for an assumed Mach number at the engine face: an estimate of how hard the
throat is working, with no losses, no boundary layer and no distortion.
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
import fieldlab as fl
import registry
from design import Design
from oml import Airframe, T_FACE, T_LIP, R_FACE, Z_ENGINE, LREF

FT, IN, LB, KT = 0.3048, 0.0254, 0.45359237, 0.514444
G, R = 1.4, 287.053


def isa(h):
    if h <= 11000:
        t = 288.15 - 0.0065 * h
        p = 101325.0 * (t / 288.15) ** 5.25588
    else:
        t = 216.65
        p = 22632.1 * math.exp(-(h - 11000) / 6341.62)
    return t, p


def flow_function(m):
    """mass flow * sqrt(T0) / (A p0)"""
    return math.sqrt(G / R) * m * (1 + 0.2 * m * m) ** -3.0


def mach_from_flow(ff):
    """Subsonic Mach number with the given flow function; None when the area is too small (choked)."""
    lo, hi = 0.0, 1.0
    if ff > flow_function(1.0):
        return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if flow_function(mid) < ff else (lo, mid)
    return 0.5 * (lo + hi)


def main():
    over = {k: float(v) for k, v in (a.split('=') for a in sys.argv[1:] if '=' in a)}
    af = Airframe(Design(**over))
    L = fl.num(af.L)
    air = af.duct_air()
    lip = (af.lip_plane() * af.scale)
    h = 0.004
    half_w, z0, z1 = 0.085 * L, -0.055 * L, 0.085 * L
    y = np.arange(h / 2, half_w, h)
    z = np.arange(z0 + h / 2, z1, h)
    Y, Z = np.meshgrid(y, z, indexing='ij')
    x0, x1 = (T_LIP - 0.015) * L, T_FACE * L
    xs = np.arange(x0, x1 + 1e-9, 0.01 * L / 4)
    rows = []
    for x in xs:
        pts = np.c_[np.full(Y.size, x), Y.ravel(), Z.ravel()]
        inside = (registry.values_at(air, pts) < 0).reshape(Y.shape)
        a = 2 * inside.sum() * h * h
        if a <= 0:
            rows.append((x, 0.0, np.nan, np.nan, np.nan, np.nan))
            continue
        zc = float(Z[inside].mean())
        rows.append((x, a, zc, float(Y[inside].max() + h / 2), float(Z[inside].min() - h / 2), float(Z[inside].max() + h / 2)))
    rows = np.array(rows)
    x, a_x, zc = rows[:, 0], rows[:, 1], rows[:, 2]
    ok = a_x > 0
    slope = np.gradient(np.where(ok, zc, 0.0), x)
    slope[~ok] = 0.0
    a_n = a_x / np.sqrt(1 + slope ** 2)
    # the duct is a closed tube once the lip plane has passed: lip field negative over the whole section
    x_closed = (T_LIP * L) + 0.0
    # station where the raked lip plane meets the duct roof: the section stops growing with the rake there
    closed = []
    for xi in x:
        pts = np.c_[np.full(Y.size, xi), Y.ravel(), Z.ravel()]
        core = registry.values_at(af.duct_core() * af.scale, pts) < 0
        cut = registry.values_at(lip, pts) > 0
        closed.append(not np.any(core & cut))
    closed = np.array(closed)
    i_closed = int(np.argmax(closed))                      # first fully enclosed station
    i_throat = i_closed + int(np.argmin(a_n[i_closed:]))
    a_throat, a_face = float(a_n[i_throat]), math.pi * (R_FACE * L) ** 2
    # capture area: the largest section between the lip and the throat (the opening seen from the front)
    a_capture = float(a_x[:i_throat + 1].max())
    # line of sight: part of the engine face that a straight line parallel to the fuselage axis reaches from the inlet
    yy, zz = np.meshgrid(np.arange(h / 2, R_FACE * L, h), np.arange(Z_ENGINE * L - R_FACE * L, Z_ENGINE * L + R_FACE * L, h), indexing='ij')
    disc = (yy ** 2 + (zz - Z_ENGINE * L) ** 2) < (R_FACE * L) ** 2
    clear = disc.copy()
    for xi in np.arange(x[i_closed], x1 - 0.01, 0.02):
        pts = np.c_[np.full(yy.size, xi), yy.ravel(), zz.ravel()]
        clear &= (registry.values_at(air, pts) < 0).reshape(yy.shape)
    sight = float(clear.sum() / disc.sum())
    length = x1 - x[i_throat]
    offset = Z_ENGINE * L - zc[i_throat]
    d_face = 2 * R_FACE * L
    geo = dict(lower_lip_station_m=T_LIP * L, first_closed_station_m=float(x[i_closed]), throat_station_m=float(x[i_throat]), engine_face_station_m=x1,
               capture_area_m2=float(a_capture), throat_area_m2=a_throat, engine_face_area_m2=a_face, engine_face_diameter_m=d_face,
               contraction_capture_to_throat=float(a_capture / a_throat), diffuser_area_ratio_face_to_throat=a_face / a_throat,
               length_throat_to_face_m=float(length), centreline_rise_m=float(offset), length_over_face_diameter=float(length / d_face),
               offset_over_length=float(offset / length), steepest_centreline_slope_deg=float(np.degrees(np.arctan(np.abs(slope[i_closed:]).max()))),
               engine_face_seen_straight_through_the_inlet_fraction=sight,
               throat_width_m=float(2 * rows[i_throat, 3]), throat_height_m=float(rows[i_throat, 5] - rows[i_throat, 4]))
    # one-dimensional Mach numbers
    cases = []
    for name, alt_ft, m0 in (('Sea level, static', 0.0, 0.0), ('Sea level, Mach 0.3', 0.0, 0.3), ('35,000 ft, Mach 0.85', 35000.0, 0.85)):
        t, p = isa(alt_ft * FT)
        t0, p0 = t * (1 + 0.2 * m0 * m0), p * (1 + 0.2 * m0 * m0) ** 3.5
        for mf in (0.35, 0.45, 0.55):
            ff = flow_function(mf)
            mdot = ff * a_face * p0 / math.sqrt(t0)
            mt = mach_from_flow(ff * a_face / a_throat)
            rec = dict(condition=name, engine_face_mach=mf, mass_flow_kg_s=mdot, throat_mach=mt)
            if m0 > 0:
                a0 = mdot * math.sqrt(t0) / (p0 * flow_function(m0))
                rec['stream_tube_area_m2'] = a0
                rec['capture_ratio_stream_tube_to_capture_area'] = a0 / a_capture
            cases.append(rec)
    out = dict(inputs=af.d.values, method='cuts of the duct air body at constant station, 4 mm grid; area normal to the centroid line; isentropic one-dimensional flow (estimate)',
               geometry=geo, stations=[dict(station_m=float(a), area_normal_m2=float(b), area_cut_m2=float(c), centroid_height_m=None if np.isnan(d) else float(d))
                                       for a, b, c, d in zip(x, a_n, a_x, zc)], flow=cases)
    res = ROOT / 'analysis' / 'results'
    res.mkdir(parents=True, exist_ok=True)
    (res / 'duct.json').write_text(json.dumps(out, indent=1))
    md = ['# Inlet duct (estimate)', '',
          'Cuts of the duct air body of the model. Areas are normal to the duct centreline. Mach numbers are one-dimensional, isentropic, for an assumed',
          'Mach number at the engine face; no losses, boundary layer or distortion.', '',
          '| Quantity | Value |', '|---|---:|',
          f"| Lower lip station | {geo['lower_lip_station_m'] / FT:.2f} ft |",
          f"| Throat station | {geo['throat_station_m'] / FT:.2f} ft |",
          f"| Engine face station | {geo['engine_face_station_m'] / FT:.2f} ft |",
          f"| Capture area (largest section at the lip, seen from the front) | {geo['capture_area_m2'] / IN ** 2:.0f} in2 |",
          f"| Throat area | {geo['throat_area_m2'] / IN ** 2:.0f} in2 ({geo['throat_width_m'] / IN:.1f} in wide, {geo['throat_height_m'] / IN:.1f} in high) |",
          f"| Engine face area | {geo['engine_face_area_m2'] / IN ** 2:.0f} in2 ({d_face / IN:.1f} in diameter) |",
          f"| Capture area / throat area | {geo['contraction_capture_to_throat']:.2f} |",
          f"| Engine face area / throat area | {geo['diffuser_area_ratio_face_to_throat']:.2f} |",
          f"| Length, throat to engine face | {length / FT:.2f} ft = {geo['length_over_face_diameter']:.1f} face diameters |",
          f"| Centreline rise, throat to engine face | {offset / IN:.1f} in = {geo['offset_over_length']:.2f} of the length |",
          f"| Steepest centreline slope | {geo['steepest_centreline_slope_deg']:.0f} deg |",
          f"| Engine face seen straight through the inlet | {sight * 100:.0f} % |", '',
          '| Condition | Engine face Mach (assumed) | Air flow [lb/s] | Throat Mach | Stream tube / capture area |', '|---|---:|---:|---:|---:|']
    for c in cases:
        tm = 'choked' if c['throat_mach'] is None else f"{c['throat_mach']:.2f}"
        cr = f"{c['capture_ratio_stream_tube_to_capture_area']:.2f}" if 'capture_ratio_stream_tube_to_capture_area' in c else 'static'
        md.append(f"| {c['condition']} | {c['engine_face_mach']:.2f} | {c['mass_flow_kg_s'] / LB:.0f} | {tm} | {cr} |")
    (res / 'duct.md').write_text('\n'.join(md))
    print('\n'.join(md))
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, gridspec_kw=dict(height_ratios=[1.25, 1]))
        st = x / FT
        ax[0].plot(st[ok], a_n[ok] / IN ** 2, color='#1f5f8b', lw=2)
        ax[0].axvline(x[i_throat] / FT, color='#888', lw=0.8, ls='--')
        ax[0].annotate(f"throat {a_throat / IN ** 2:.0f} in2", (x[i_throat] / FT, a_throat / IN ** 2), textcoords='offset points', xytext=(8, -16), fontsize=9)
        ax[0].annotate(f"engine face {a_face / IN ** 2:.0f} in2", (x1 / FT, a_face / IN ** 2), textcoords='offset points', xytext=(-110, 6), fontsize=9)
        ax[0].set_ylabel('Duct area normal to the centreline [in2]')
        ax[0].set_ylim(0, None)
        ax[0].grid(alpha=0.25)
        ax[0].set_title('Fury model: inlet duct area distribution and centreline (estimate)', fontsize=11, loc='left')
        ax[1].fill_between(st[ok], rows[ok, 4] / IN, rows[ok, 5] / IN, color='#cfe0ec', label='duct, lowest to highest point of the section')
        ax[1].plot(st[ok], zc[ok] / IN, color='#1f5f8b', lw=2, label='centroid of the section')
        ax[1].set_xlabel('Station aft of the nose tip [ft]')
        ax[1].set_ylabel('Height above the reference line [in]')
        ax[1].grid(alpha=0.25)
        ax[1].legend(fontsize=8, frameon=False, loc='upper left')
        fig.tight_layout()
        fig.savefig(res / 'duct.png', dpi=150)
    except Exception as e:                                  # the numbers do not depend on the picture
        print('no plot:', e)


if __name__ == '__main__':
    main()
