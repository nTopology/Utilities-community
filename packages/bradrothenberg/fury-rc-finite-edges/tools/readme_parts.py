"""Fill the generated parts of README.md and docs/PACKAGE_README.md from the current results.

A generated part sits between two marker lines:   <!--NAME-->   ...   <!--/NAME-->
Called by tools/write_docs.py.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FT, IN, LB, GAL = 0.3048, 0.0254, 0.45359237, 0.003785411784


def _load(path):
    p = ROOT / path
    return json.loads(p.read_text()) if p.exists() else None


def parts():
    out = {}
    pres = _load('native/notebook/fury_presentation.json')
    import sys
    sys.path.insert(0, str(ROOT / 'model'))
    import design
    n_inputs = len(design.INPUTS)
    if pres:
        out['COUNTS'] = (f"- {pres['final_bodies']} bodies, {pres['variables']} variables in {len(pres['sections'])} sections, every section with a description, "
                         f"{'no block uses anything defined below it' if not pres['variables_used_before_they_are_defined'] else 'some blocks use variables defined below them'}.")
    out['INPUTS'] = (f"- **{n_inputs} inputs** in ft, in, deg and %: size, wing and tail planforms, inlet, diverter and splitter plate, skin and web thickness, "
                     "spar positions, panel lines (`docs/INPUTS.md`).")
    match = _load('.local/match_final/match.json')
    if match:
        rows = ['| Check | Result |', '|---|---|']
        label = {'side_07': 'Side view, USAF photograph 07', 'plan_01': 'Plan view, Anduril photograph 01 (oblique)'}
        for r in sorted(match, key=lambda r: r['view'], reverse=True):
            d = r['outline_distance_percent_length']
            med = d['photo_to_model_median']
            med = f'{med:.2f} % of the length' if med >= 0.005 else 'one pixel of the photograph'
            rows.append(f"| {label.get(r['view'], r['view'])} | silhouette overlap {r['overlap_iou'] * 100:.1f} %, outline within {med} (median) "
                        f"and {d['photo_to_model_p90']:.2f} % of the length (90 % of the outline) |")
        rows.append('| Size | 33.5 ft long, 24.85 ft span, from the AIM-120 carried in photograph 07 (no dimensions are published) |')
        out['MATCH'] = '\n'.join(rows)
    lines = []
    mass = _load('analysis/results/mass.json')
    if mass:
        t, g = mass['totals'], mass['geometry']
        mac, x0 = g['reference_wing']['mean_aerodynamic_chord_m'], g['reference_wing']['mac_leading_edge_station_m']
        pct = lambda x: (x - x0) / mac * 100
        lines.append(f"- **Weights of the modelled items:** structure {t['structure_kg'] / LB:,.0f} lb, engine and jet pipe {t['engine_kg'] / LB:,.0f} lb, usable fuel "
                     f"{t['usable_fuel_m3'] / GAL:,.0f} US gal = {t['usable_fuel_kg'] / LB:,.0f} lb (packing limit of the bays). Full fuel {t['modelled_with_full_fuel_kg'] / LB:,.0f} lb with the "
                     f"centre of gravity at station {t['modelled_with_full_fuel_cg_m'][0] / FT:.2f} ft ({pct(t['modelled_with_full_fuel_cg_m'][0]):.0f} % of the mean aerodynamic chord); "
                     f"no landing gear, systems or payload are in these numbers. Wetted area {g['wetted_area_m2'] / FT ** 2:.0f} ft2, reference wing {g['reference_wing']['area_m2'] / FT ** 2:.1f} ft2.")
    duct = _load('analysis/results/duct.json')
    if duct:
        g = duct['geometry']
        lines.append(f"- **Inlet duct:** capture {g['capture_area_m2'] / IN ** 2:.0f} in2, throat {g['throat_area_m2'] / IN ** 2:.0f} in2, engine face {g['engine_face_area_m2'] / IN ** 2:.0f} in2 "
                     f"(face / throat {g['diffuser_area_ratio_face_to_throat']:.2f}), {g['length_over_face_diameter']:.1f} face diameters long, centreline rise "
                     f"{g['centreline_rise_m'] / IN:.1f} in, {g['engine_face_seen_straight_through_the_inlet_fraction'] * 100:.0f} % of the engine face visible straight through the inlet.")
    vlm = _load('analysis/results/vlm.json')
    if vlm:
        r = {(x['tail'], x['mach']): x for x in vlm['results']}
        keys = sorted({k[0] for k in r})
        m0 = min(k[1] for k in r)
        txt = '; '.join(f"{k.lower()}: lift slope {r[(k, m0)]['cl_alpha_per_deg']:.4f} per deg, neutral point at station {r[(k, m0)]['neutral_point_station_m'] / FT:.2f} ft "
                        f"({r[(k, m0)]['neutral_point_percent_mac']:.0f} % MAC)" for k in keys)
        lines.append(f"- **Vortex lattice (lifting surfaces only, Mach {m0:g}):** {txt}.")
    cfd = _load('analysis/results/cfd.json')
    if cfd and cfd.get('runs'):
        txt = ', '.join(f"alpha {x['alpha_deg']:.0f} deg: CL {x['summary']['cl_q']:.3f}, CD {x['summary']['cd_q']:.4f}, Cm {x['summary']['cm_q']:+.3f}" for x in cfd['runs'])
        extra = ''
        if cfd.get('fits'):
            f = cfd['fits']
            extra = f" Lift slope {f['lift_slope_per_deg']:.4f} per deg, neutral point at station {f['neutral_point_station_m'] / FT:.2f} ft."
        lines.append(f"- **Flow solution (lattice Boltzmann, half model, inlet and nozzle faired over):** {txt}.{extra} See the note in `docs/ANALYSIS.md` on which geometry revision was run.")
    else:
        lines.append('- **Flow solution:** the case is prepared (`analysis/cfd`), no run has finished.')
    compare = methods_compared()
    if compare:
        lines.append('- **The two aerodynamic estimates do not agree:** ' + compare)
    check = native_check()
    if check:
        lines.append('- **Notebook against the Python model:** ' + check)
    out['ANALYSIS'] = '\n'.join(lines)
    return out


def methods_compared():
    """Vortex lattice against the flow solution, and what that means for the centre of gravity (conventional tail)."""
    vlm, cfd, mass = _load('analysis/results/vlm.json'), _load('analysis/results/cfd.json'), _load('analysis/results/mass.json')
    if not (vlm and cfd and cfd.get('fits') and mass):
        return ''
    low = min(x['mach'] for x in vlm['results'])
    lat = next(x for x in vlm['results'] if x['mach'] == low and x['tail'].lower().startswith('conventional'))
    f = cfd['fits']
    mac = mass['geometry']['reference_wing']['mean_aerodynamic_chord_m']
    cg = mass['totals']['modelled_with_full_fuel_cg_m'][0]
    np_l, np_f = lat['neutral_point_station_m'], f['neutral_point_station_m']
    return (f"the vortex lattice (wing and tail only, no fuselage) gives a lift slope of {lat['cl_alpha_per_deg']:.4f} per deg and a neutral point at station {np_l / FT:.2f} ft; "
            f"the flow solution of the whole aircraft gives {f['lift_slope_per_deg']:.4f} per deg and station {np_f / FT:.2f} ft, {(np_l - np_f) / FT:.1f} ft "
            f"({(np_l - np_f) / mac * 100:.0f} % of the mean aerodynamic chord) further forward. A long, wide forebody with chines does move the neutral point forward, "
            "but the flow solution is two angles on one grid with no grid study, so neither number is settled. "
            f"The full-fuel centre of gravity of the modelled items (station {cg / FT:.2f} ft) is at the lattice neutral point and {(cg - np_f) / mac * 100:.0f} % of the chord "
            "behind the flow-solution one: as modelled, with every bay full and no landing gear, systems or payload, the aircraft is not shown to be statically stable. "
            "Treat the centre of gravity and stability as open.")


def native_check():
    """One paragraph on the nTop meshes of the outer mold line compared with the Python model."""
    ver = [_load('native/pilot/exterior_verify.json'), _load('native/pilot/exterior_tail_type1_verify.json')]
    if not all(ver):
        return ''
    old = _load('native/pilot/exterior_verify_before_diverter.json')
    current = bool(old) and old['triangles'] != ver[0]['triangles']
    mil = lambda m: m / IN * 1000
    one = lambda v: (f"{v['triangles'] / 1e6:.1f} M triangles, 99 % of the vertices within {mil(v['host_abs_p99_m']):.1f} thousandths of an inch of the Python field, "
                     f"largest difference {v['host_abs_max_m'] / IN:.2f} in")
    return (f"the outer mold line was meshed in nTop at a tolerance of {ver[0]['tolerance_m'] / IN:.2f} in and the Python field evaluated at every mesh vertex. "
            f"Conventional tail ({'the final shape with diverter and splitter plate' if current else 'before the diverter and splitter plate were added'}): {one(ver[0])}. "
            f"V-tail (before the diverter and splitter plate were added): {one(ver[1])}. Panel grooves and paint films are not part of the outer mold line "
            "and were not meshed in nTop.")


def fill(path, values):
    p = ROOT / path
    if not p.exists():
        return
    s = p.read_text(encoding='utf-8')
    for name, body in values.items():
        s = re.sub(rf'<!--{name}-->.*?<!--/{name}-->', lambda m: f'<!--{name}-->\n{body}\n<!--/{name}-->', s, flags=re.S)
    p.write_text(s, encoding='utf-8')


def run():
    values = parts()
    for path in ('README.md', 'docs/PACKAGE_README.md'):
        fill(path, values)
    return values


if __name__ == '__main__':
    for k, v in run().items():
        print(f'--- {k}\n{v}')
