"""Volumes, weights and centre of gravity of the modelled bodies.

  python analysis/mass.py [key=value ...]        ->  analysis/results/mass[_<tag>].json and .md

Volumes and centroids come from closed meshes of the bodies (tetrahedra to the origin). The skin is the wetted
area of the outer mold line times the skin thickness. Densities, the engine weight and the usable-fuel fraction
are assumptions written in the output. Everything shown is in US customary units; the json keeps SI as well.
The structure is a representative layout, so the weights are estimates and not a weight statement.
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
import fieldlab as fl
import aircraft, registry
from design import Design
from oml import T_FACE

FT, IN, LB, GAL = 0.3048, 0.0254, 0.45359237, 3.785411784e-3
ASSUME = dict(
    skin_density=1600.0,          # kg/m3, carbon/epoxy laminate
    structure_density=2770.0,     # kg/m3, aluminium alloy frames, spars and ribs
    jet_pipe_density=4430.0,      # kg/m3, titanium sheet
    fuel_density=804.0,           # kg/m3, JP-8 at 15 C (6.71 lb/gal)
    usable_fuel_fraction=0.88,    # of the geometric cell volume: bladder walls, internal structure, ullage and unusable fuel
    engine_weight_lb=650.0,       # Williams FJ44-4A dry weight as published by the maker (the Fury engine is reported as an FJ44-4 variant)
    landing_gear_fraction=0.04,   # landing gear weight as a share of the weight with full fuel (handbook values for jets run 3 to 5 %)
    engine_thrust_lbf=4000.0,     # Williams FJ44-4M as reported for the Fury (about 4,000 lbf)
)


def solid(v, f):
    """Volume and centroid of a closed mesh (or a half mesh open on the plane y = 0)."""
    a, b, c = v[f[:, 0]].astype(np.float64), v[f[:, 1]].astype(np.float64), v[f[:, 2]].astype(np.float64)
    vol = np.einsum('ij,ij->i', a, np.cross(b, c)) / 6.0
    cen = (a + b + c) / 4.0
    V = vol.sum()
    return abs(V), (cen * vol[:, None]).sum(0) / V


def area(v, f):
    a, b, c = v[f[:, 0]].astype(np.float64), v[f[:, 1]].astype(np.float64), v[f[:, 2]].astype(np.float64)
    n = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    return n.sum(), (((a + b + c) / 3.0) * n[:, None]).sum(0) / n.sum()


def d_gear_station(m):
    """Station of the main gear (used when the gear is retracted and has no bodies)."""
    return m.d.value('main_gear_station') * 0.01 * fl.num(m.L)


def main():
    over = {k: float(v) for k, v in (a.split('=') for a in sys.argv[1:] if '=' in a)}
    tag = '_'.join(f'{k}{v:g}' for k, v in over.items())
    ac = aircraft.build(Design(**over))
    m = ac.model
    L = fl.num(m.L)
    rows = []

    def add(name, group, vol, cen, density, note='', weight=None):
        w = vol * density if weight is None else weight
        rows.append(dict(body=name, group=group, volume_m3=vol, centroid_m=[float(c) for c in cen], density_kg_m3=density, mass_kg=w, note=note))

    # outer mold line: wetted area, enclosed volume
    sk = next(p for p in ac.parts if p.name == 'Skin')
    lo = [sk.lo[0], 0.0, sk.lo[2]]
    v, f, _ = registry.surface_mesh(m.exterior, lo, sk.hi, sk.h, 'exterior')
    wet_half, wet_c = area(v, f)
    ext_half, ext_c = solid(v, f)
    wet = 2 * wet_half
    t_skin = fl.num(m.skin_t)
    add('Skin', 'structure', wet * t_skin, [wet_c[0], 0.0, wet_c[2]], ASSUME['skin_density'], 'wetted area x skin thickness')
    gear = []
    for p in ac.parts:
        if p.name in ('Skin', 'Air data boom') or p.group in ('paint', 'fittings'):
            continue                                     # pylons, rails, missiles, antennas and the scoop are not weighed
        if p.group == 'gear':
            v, f, _ = registry.mesh_part(p)
            if len(f):
                gear.append(solid(v, f))
            continue
        if p.group == 'fuel' or p.name in ('Mission systems bay', 'Inlet duct air'):
            half = registry.Part(p.name + ' (starboard half)', fl.fmax(p.field, -fl.Y), p.mat, p.section, p.lo, p.hi, p.h, p.group)
            v, f, _ = registry.mesh_part(half)
            vol, c = solid(v, f)
            vol, c = 2 * vol, [c[0], 0.0, c[2]]
        else:
            v, f, _ = registry.mesh_part(p)
            vol, c = solid(v, f)
            c = [c[0], 0.0, c[2]]
        if p.group == 'fuel':
            add(p.name, 'fuel', vol, c, ASSUME['fuel_density'] * ASSUME['usable_fuel_fraction'], 'usable fuel = cell volume x usable fraction')
        elif p.name == 'Engine':
            add(p.name, 'engine', vol, c, 0.0, 'published dry weight, placed at the centroid of the envelope', weight=ASSUME['engine_weight_lb'] * LB)
        elif p.name == 'Jet pipe':
            add(p.name, 'engine', vol, c, ASSUME['jet_pipe_density'])
        elif p.name in ('Mission systems bay', 'Inlet duct air'):
            add(p.name, 'volume only', vol, c, 0.0, 'space, no weight assigned')
        else:
            add(p.name, 'structure', vol, c, ASSUME['structure_density'])

    def total(group):
        r = [x for x in rows if x['group'] == group]
        w = sum(x['mass_kg'] for x in r)
        c = np.sum([np.array(x['centroid_m']) * x['mass_kg'] for x in r], axis=0) / w
        return w, c

    ws, cs = total('structure')
    we, ce = total('engine')
    wf, cf = total('fuel')
    fuel_vol = sum(x['volume_m3'] for x in rows if x['group'] == 'fuel')
    # landing gear: an assumed share of the full weight, placed at the centroid of the gear bodies
    k = ASSUME['landing_gear_fraction']
    wg = k / (1 - k) * (ws + we + wf)
    if gear:
        cg = np.sum([c * v for v, c in gear], axis=0) / sum(v for v, c in gear)
        cg = np.array([cg[0], 0.0, cg[2]])
    else:
        cg = np.array([d_gear_station(m), 0.0, 0.0])
    add('Landing gear (legs, wheels, tyres, doors)', 'gear', sum(v for v, c in gear), cg, 0.0, f'assumed {k * 100:.0f} % of the weight with full fuel', weight=wg)
    w_no_fuel, c_no_fuel = ws + we + wg, (cs * ws + ce * we + cg * wg) / (ws + we + wg)
    w_full, c_full = ws + we + wg + wf, (cs * ws + ce * we + cg * wg + cf * wf) / (ws + we + wg + wf)
    # reference wing: the trapezoid of the inputs carried to the centreline
    d = m.d
    b = d.value('wing_span') * FT
    cr, ct = d.value('wing_root_chord') * FT, d.value('wing_tip_chord') * FT
    S = 0.5 * (cr + ct) * b
    lam = ct / cr
    mac = 2 / 3 * cr * (1 + lam + lam * lam) / (1 + lam)
    y_mac = b / 6 * (1 + 2 * lam) / (1 + lam)
    x_mac_le = d.value('wing_apex') * 0.01 * L + y_mac * np.tan(np.radians(d.value('wing_sweep')))
    out = dict(
        inputs=d.values, assumptions=ASSUME,
        geometry=dict(length_m=L, span_m=b, wetted_area_m2=wet, enclosed_volume_m3=2 * ext_half, enclosed_volume_centroid_station_m=float(ext_c[0]),
                      reference_wing=dict(area_m2=S, span_m=b, aspect_ratio=b * b / S, taper=lam, mean_aerodynamic_chord_m=mac,
                                          mac_leading_edge_station_m=float(x_mac_le), definition='trapezoid of the wing inputs carried to the centreline')),
        bodies=rows,
        totals=dict(landing_gear_kg=wg, landing_gear_cg_m=cg.tolist(), structure_kg=ws, structure_cg_m=cs.tolist(), engine_kg=we, engine_cg_m=ce.tolist(),
                    fuel_cell_volume_m3=fuel_vol, usable_fuel_m3=fuel_vol * ASSUME['usable_fuel_fraction'], usable_fuel_kg=wf, fuel_cg_m=cf.tolist(),
                    modelled_without_fuel_kg=w_no_fuel, modelled_without_fuel_cg_m=c_no_fuel.tolist(),
                    modelled_with_full_fuel_kg=w_full, modelled_with_full_fuel_cg_m=c_full.tolist(),
                    thrust_over_modelled_weight_full_fuel=ASSUME['engine_thrust_lbf'] * LB / w_full),
    )
    res = ROOT / 'analysis' / 'results'
    res.mkdir(parents=True, exist_ok=True)
    name = 'mass' + ('_' + tag if tag else '')
    (res / f'{name}.json').write_text(json.dumps(out, indent=1))

    def pct(x):
        return (x - x_mac_le) / mac * 100

    lines = ['# Weights, fuel and centre of gravity (estimate)', '',
             'Bodies of the model with assumed densities. The structure is a representative layout, not a stressed design: read these as',
             'first estimates. Stations are measured aft of the nose tip.', '',
             f'- Length {L / FT:.1f} ft, span {b / FT:.2f} ft, wetted area {wet / FT ** 2:.0f} ft2, enclosed volume {2 * ext_half / FT ** 3:.0f} ft3',
             f'- Reference wing (input trapezoid to the centreline): area {S / FT ** 2:.1f} ft2, aspect ratio {b * b / S:.2f}, taper {lam:.3f}, '
             f'mean aerodynamic chord {mac / FT:.2f} ft with its leading edge at station {x_mac_le / FT:.2f} ft', '',
             '| Body | Volume [ft3] | Weight [lb] | Station of centroid [ft] | Height [in] | Basis |', '|---|---:|---:|---:|---:|---|']
    for x in rows:
        lines.append(f"| {x['body']} | {x['volume_m3'] / FT ** 3:.2f} | {x['mass_kg'] / LB:.0f} | {x['centroid_m'][0] / FT:.2f} | {x['centroid_m'][2] / IN:.1f} | "
                     f"{x['note'] or ('%.0f lb/ft3' % (x['density_kg_m3'] / LB * FT ** 3))} |")
    lines += ['', '| Total | Weight [lb] | Centre of gravity station [ft] | % of mean aerodynamic chord |', '|---|---:|---:|---:|',
              f'| Structure (skin, frames, spars, ribs) | {ws / LB:.0f} | {cs[0] / FT:.2f} | {pct(cs[0]):.0f} |',
              f'| Engine and jet pipe | {we / LB:.0f} | {ce[0] / FT:.2f} | {pct(ce[0]):.0f} |',
              f'| Landing gear (assumed {k * 100:.0f} % of full weight) | {wg / LB:.0f} | {cg[0] / FT:.2f} | {pct(cg[0]):.0f} |',
              f'| Usable fuel ({fuel_vol * ASSUME["usable_fuel_fraction"] / GAL:.0f} US gal) | {wf / LB:.0f} | {cf[0] / FT:.2f} | {pct(cf[0]):.0f} |',
              f'| Modelled items, no fuel | {w_no_fuel / LB:.0f} | {c_no_fuel[0] / FT:.2f} | {pct(c_no_fuel[0]):.0f} |',
              f'| Modelled items, full fuel | {w_full / LB:.0f} | {c_full[0] / FT:.2f} | {pct(c_full[0]):.0f} |', '',
              f'Fuel cells hold {fuel_vol / GAL:.0f} US gal geometric volume; {ASSUME["usable_fuel_fraction"] * 100:.0f} % is counted usable: {wf / LB:.0f} lb of JP-8.',
              'This is the packing limit of the model: every fuselage bay between the tank bulkheads is filled except the landing gear bays, and so is the wing box.',
              'A real aircraft gives more of that space to systems and weapons, so its fuel load is lower.',
              f'The landing gear is not weighed from its bodies: it is an assumed {k * 100:.0f} % of the weight with full fuel, placed at the centroid of the gear bodies.',
              'Systems, mission equipment, pylons and stores are not weighed, so the centre of gravity above is of the modelled items only.',
              f'With the reported {ASSUME["engine_thrust_lbf"]:.0f} lbf engine, thrust / weight of the modelled items at full fuel is {ASSUME["engine_thrust_lbf"] * LB / w_full:.2f}.',
              'The 5,000 lb maximum take-off weight often quoted for the Fury goes with the 20 ft by 17 ft size quoted for the earlier design; it is not used here',
              'because the photographs give a 33.5 ft aircraft (reference/PROPORTIONS.md).', '',
              'Assumptions: ' + ', '.join(f'{k} = {v}' for k, v in ASSUME.items()) + '.']
    (res / f'{name}.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
