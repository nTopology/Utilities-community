"""Flight statement of the Fury model: weights, balance, inertia, engine and the aerodynamic database behind the
turn-performance table (turn.py) and the 6-DOF flight model (sim/).

    python flight/aircraft.py        ->  flight/out/aircraft.json, flight/out/aircraft.md, flight/out/lattice.json

EVERYTHING HERE IS AN ESTIMATE made from the shape of this model and public figures. No dimension, weight, thrust curve
or aerodynamic coefficient of the real aircraft is published; the size of the model itself rests on one photograph.
Each number names where it comes from: the model (measured on the geometry), a public figure, a handbook method, the
lattice (flight/lattice.py), the flow solution (analysis/results/flow_points.json) or an assumption.

Frames: model frame x aft from the nose, y starboard, z up, metres. Stored values SI; shown values US customary.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'out'
sys.path.insert(0, str(HERE / 'ref'))
from common import FT, FT2, IN, LB, LBF, KT, G0, PSF, SLUG_FT2, isa  # noqa: E402

DEG = math.pi / 180.0
MACHS = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

# ----------------------------------------------------------------------------------------------------------------------
# Assumptions (one place). Change them here; every result is rebuilt from them.
# ----------------------------------------------------------------------------------------------------------------------
ASSUME = dict(
    # weights
    structure_allowance=1.30,           # on the modelled structure: joints, doors, fairings, paint, fasteners (ASSUMPTION)
    systems_lb=650.0,                   # flight controls and actuators, electrical, fuel system, hydraulics, environmental, flight computers (ASSUMPTION)
    mission_systems_lb=300.0,           # sensors and mission equipment in the nose bay (ASSUMPTION; the bay is 19 ft3 in the model)
    missile_lb=356.0,                   # one AIM-120-class missile (public figure of the AIM-120C/D)
    launcher_lb=50.0,                   # one pylon launcher (ASSUMPTION)
    fuel_fraction_combat=0.50,          # of the usable fuel the modelled cells hold; the F-16 reference is taken at 50 % internal fuel as well
    fuel_fraction_landing=0.15,
    # balance
    static_margin=0.05,                 # ASSUMPTION: the centre of gravity is 5 % of the mean chord ahead of the estimated neutral point
    # limits (public figures of the Fury programme: 9 g, Mach 0.95)
    n_limit=9.0, n_min=-3.0, mach_limit=0.95,
    # engine
    engine='Williams FJ44-4M', thrust_sl_static_lbf=3790.0, lapse_k_mach=0.30, throttle_ratio=1.04,
    inlet_recovery=0.97, ram_recovery_factor=1.35, offtake_factor=0.985, nozzle_factor=0.98, spool_time_s=1.5, idle_fraction=0.05,
    # drag
    cfe=0.0030,                         # equivalent skin friction on the wetted area: between the handbook 0.0025 (clean supersonic cruise aircraft) and 0.0035
                                        # (fighter with canopy, gun and gaps), Raymer table 12.3. With korn_kappa it is set so that the model just reaches Mach 0.9
                                        # in level flight at height (the published top speed is Mach 0.95)
    store_drag_area_ft2=0.20,           # D/q of one missile on its pylon launcher (ASSUMPTION, Raymer-class figure)
    gear_drag_area_ft2=3.2,             # D/q of the landing gear with its doors (ASSUMPTION: three legs, three wheels, open doors)
    suction_low=0.92, suction_at_clmax=0.55, suction_break=0.45,     # leading-edge suction: 92 % up to 45 % of CLmax, falling to 55 % at CLmax (thin wing, no leading-edge flap)
    korn_kappa=0.91, drag_divergence_shift=0.0,       # Korn factor between a conventional section (0.87) and a supercritical one (0.95)
    # lift limit
    cl_max_low_speed=1.10,              # ASSUMPTION: usable, trimmed, clean (no leading-edge device is modelled or assumed); plus or minus 0.15
    cl_max_mach=[0.0, 0.5, 0.7, 0.8, 0.9, 0.95], cl_max_factor=[1.0, 1.0, 0.88, 0.79, 0.71, 0.65],   # fall with Mach number: the same trend as the F-16 reference
    stall_cap_width_deg=4.0, post_stall_drop=0.15, post_stall_over_deg=6.0, drag_rise_over_deg=4.0, limiter_margin_deg=1.0,
    # controls: travel, rate, viscous factor on the lattice derivative
    stabilator_deg=[-25.0, 15.0], flaperon_deg=[-25.0, 35.0], rudder_deg=25.0, flap_landing_deg=30.0,
    surface_rate_dps=60.0, rudder_rate_dps=90.0, actuator_time_s=0.05,
    stab_k1=0.95, stab_k2=0.45, stab_break_deg=14.0,            # all-moving tail: 95 % of the lattice up to 14 deg, half beyond (tail stall)
    flap_k1=0.85, flap_k2=0.375, flap_break_deg=10.0,           # plain flap: 85 % of the lattice to 10 deg, slope 0.475 beyond
    rudder_k=0.75,
    flap_profile_drag=1.7, fin_efficiency=0.90,
    # inertia: radii of gyration of a single-engine jet fighter (Raymer, Aircraft Design, table 16.1)
    r_x=0.23, r_y=0.38, r_z=0.52, ixz_fraction_of_ixx=0.05,
)
ASSUME_NOTE = 'Assumptions of the flight statement. None is manufacturer data.'

# fuselage half width / length at stations t = x / length (model/oml.py HALF_WIDTH, the chine line) for the body pitching-moment estimate
BODY_T = [0.0, 0.03, 0.06, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0]
BODY_HALF_WIDTH = [0.0008, 0.0105, 0.0200, 0.0315, 0.0445, 0.0560, 0.0660, 0.0720, 0.0755, 0.0775, 0.0785, 0.0790,
                   0.0790, 0.0788, 0.0780, 0.0765, 0.0735, 0.0690, 0.0635, 0.0555, 0.0450, 0.0340]


def _load(name):
    return json.loads((ROOT / 'analysis' / 'results' / name).read_text())


USE_CURRENT_SHAPE_FLOW = True


def flow_points():
    """Points of the flow solution on the current shape (analysis/results/flow_points.json), if any:
    [(alpha deg, CL, CD, Cm about the quarter chord, converged)]."""
    f = ROOT / 'analysis' / 'results' / 'flow_points.json'
    if not f.exists():
        return []
    return sorted((float(p['alpha_deg']), float(p['cl']), float(p['cd']), float(p['cm_quarter_chord']), bool(p['converged']))
                  for p in json.loads(f.read_text())['points'])


# ----------------------------------------------------------------------------------------------------------------------
def lattice_table(rebuild=False):
    """Lattice derivatives at the Mach numbers of the database, at zero lift and at 0.1 rad (cached in out/lattice.json)."""
    f = OUT / 'lattice.json'
    if f.exists() and not rebuild:
        return json.loads(f.read_text())
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(ROOT / 'model'))
    import lattice
    from design import Design
    d = Design()
    ref = lattice.base.reference(d)
    rows = []
    for m in MACHS:
        lat = lattice.Lattice(d, m)
        off = lattice.Lattice(d, m, tail=False)
        d0, d1 = lat.derivatives(0.0), lat.derivatives(0.1)
        o0 = off.derivatives(0.0)
        rows.append(dict(mach=m, at_zero_lift={c: {k: float(v) for k, v in d0[c].items()} for c in ('CL', 'CY', 'Cl', 'Cm', 'Cn')},
                         at_alpha_0p1={c: {k: float(v) for k, v in d1[c].items()} for c in ('CL', 'CY', 'Cl', 'Cm', 'Cn')}, cl_at_alpha_0p1=float(d1['CL0']),
                         tail_off=dict(cl_alpha=float(o0['CL']['alpha']), cm_alpha=float(o0['Cm']['alpha']))))
        print('lattice Mach %.1f: CL alpha %.3f, Cm alpha %.3f' % (m, d0['CL']['alpha'], d0['Cm']['alpha']), flush=True)
    v = d.value
    out = dict(what='vortex-lattice derivatives of the planform inputs (flight/lattice.py): estimate, no fuselage, thickness, camber or viscosity',
               moment_point='quarter of the mean aerodynamic chord; rates turn about the same point',
               reference=dict(S=ref['S'], b=ref['b'], mac=ref['mac'], x_mac_le=ref['x_mac_le'], length=ref['L']),
               planform={k: v(k) for k in ('length', 'wing_span', 'wing_root_chord', 'wing_tip_chord', 'wing_sweep', 'wing_apex', 'wing_tc_root', 'wing_tc_tip',
                                           'htail_span', 'htail_root_chord', 'htail_tip_chord', 'htail_apex', 'fin_height', 'fin_root_chord', 'fin_tip_chord',
                                           'nose_gear_station', 'main_gear_station', 'gear_track', 'nozzle_diameter')},
               check=lattice.check(), rows=rows)
    OUT.mkdir(exist_ok=True)
    f.write_text(json.dumps(out, indent=1))
    return out


def body_moment_slope(ref, cla_wing, lh, deda):
    """dCm/dalpha of the fuselage per rad (Multhopp strip method as in Roskam/Raymer: width squared times the local upwash or
    downwash gradient, summed along the length). Estimate: a slender-body method on a wide chined body."""
    L, S, c = ref['length'], ref['S'], ref['mac']
    t = np.linspace(0.0, 1.0, 401)
    w = 2.0 * np.interp(t, BODY_T, BODY_HALF_WIDTH) * L
    x = t * L
    v = PLAN
    x_le = v['wing_apex'] * 0.01 * L
    x_te = x_le + v['wing_root_chord'] * FT
    cr = v['wing_root_chord'] * FT
    grad = np.zeros_like(x)
    ahead = x < x_le
    xi = np.maximum((x_le - x[ahead]) / cr, 0.05)
    grad[ahead] = (1.0 + 0.17 / xi ** 0.9) * (cla_wing / (0.0785 / DEG))          # upwash ahead of the wing, fitted to the Multhopp curve
    behind = x > x_te
    grad[behind] = np.clip((x[behind] - x_te) / lh, 0.0, 1.5) * (1.0 - deda)      # behind the wing: rises linearly to (1 - downwash gradient) at the tail
    per_deg = np.trapezoid(w * w * grad, x) / (36.5 * S * c)
    return float(per_deg / DEG)


# ----------------------------------------------------------------------------------------------------------------------
def build():
    """The flight statement as one dict (SI)."""
    global PLAN
    A = ASSUME
    lat = lattice_table()
    PLAN = lat['planform']
    ref = lat['reference']
    S, b, c, L = ref['S'], ref['b'], ref['mac'], ref['length']
    x_ref = ref['x_mac_le'] + 0.25 * c
    mass = _load('mass.json')
    T, G = mass['totals'], mass['geometry']
    vl = _load('vlm.json')['geometry']

    # ---- weights
    lb = lambda kg: kg / LB
    structure = lb(T['structure_kg']) * A['structure_allowance']
    engine = lb(T['engine_kg'])
    gear = lb(T['landing_gear_kg'])
    empty = structure + engine + gear + A['systems_lb'] + A['mission_systems_lb']
    fuel_max = lb(T['usable_fuel_kg'])
    stores = 2 * (A['missile_lb'] + A['launcher_lb'])
    cases = {}
    for key, frac, with_stores, label in (('combat', A['fuel_fraction_combat'], True, '50 % fuel, two missiles'),
                                           ('landing', A['fuel_fraction_landing'], True, '15 % fuel, two missiles'),
                                           ('takeoff', 1.0, True, 'full fuel, two missiles'),
                                           ('light', None, True, '5,000 lb: the gross weight published for the original Fury design')):
        w = 5000.0 if frac is None else empty + (stores if with_stores else 0.0) + frac * fuel_max
        m = w * LB
        cases[key] = dict(label=label, weight_lb=w, mass_kg=m, fuel_lb=None if frac is None else frac * fuel_max, wing_loading_lb_ft2=w / (S / FT2),
                          inertia=dict(ixx=(b * A['r_x'] / 2) ** 2 * m, iyy=(L * A['r_y'] / 2) ** 2 * m, izz=((b + L) / 2 * A['r_z'] / 2) ** 2 * m,
                                       ixz=A['ixz_fraction_of_ixx'] * (b * A['r_x'] / 2) ** 2 * m))
    weights = dict(
        structure_lb=structure, structure_note='modelled structure %.0f lb (analysis/results/mass.json, measured on the model) x %.2f allowance' % (lb(T['structure_kg']), A['structure_allowance']),
        engine_lb=engine, engine_note='engine and jet pipe as in analysis/results/mass.json (engine weight assumed there from the public FJ44-4 figure)',
        landing_gear_lb=gear, systems_lb=A['systems_lb'], mission_systems_lb=A['mission_systems_lb'], empty_lb=empty,
        usable_fuel_lb=fuel_max, fuel_note='what the modelled fuel cells hold (%.0f US gal); the real fuel load is not published' % (T['usable_fuel_m3'] / 0.003785411784),
        stores_lb=stores, stores_note='two AIM-120-class missiles on pylon launchers, as in the photographs the model was matched to',
        cases=cases,
        inertia_note='radii of gyration of a single-engine jet fighter (Raymer table 16.1: 0.23, 0.38, 0.52 of half span, half length and their mean); Ixz 5 % of Ixx (ASSUMPTION)',
        statement='ESTIMATE. The real weights are not published. The one public figure, 5,000 lb gross weight, was given for the original, smaller Fury design; '
                  'it is carried as the "light" case.')

    # ---- engine
    install = (1 - A['ram_recovery_factor'] * (1 - A['inlet_recovery'])) * A['offtake_factor'] * A['nozzle_factor']
    eng_x = T['engine_cg_m'][0] if 'engine_cg_m' in T else 8.39
    eng_z = T['engine_cg_m'][2] if 'engine_cg_m' in T else 0.347
    engine_d = dict(name=A['engine'], thrust_sl_static_N=A['thrust_sl_static_lbf'] * LBF, install_factor=install,
                    thrust_installed_sl_static_N=A['thrust_sl_static_lbf'] * LBF * install,
                    lapse=dict(eng_w_matt=1.0, eng_w_dens=0.0, eng_k_m=A['lapse_k_mach'], eng_k_theta=3.0, eng_tr=A['throttle_ratio'], eng_c_t=0.0, eng_c_0=1.5, eng_c_m=1.0,
                               eng_n_sig=0.7, eng_a1=0.0, eng_a2=0.0),
                    thrust_line_z_m=eng_z, thrust_point_m=[eng_x, 0.0, eng_z],
                    source='Thrust 3,790 lbf sea-level static: public figure of the FJ44-4M (Aero L-39NG data); the FJ44-4M is the engine publicly named for the YFQ-44A. '
                           'Lapse with speed and height: Mattingly, Heiser and Pratt high-bypass form with the Mach term reduced to 0.30 for a bypass ratio of 3 to 4 (ASSUMPTION), '
                           'flat rated to a throttle ratio of 1.04. Installation: (1 - 1.35 x (1 - recovery)) x offtake x nozzle = %.3f with an assumed inlet recovery of %.2f. '
                           'No afterburner. Uncertainty about plus or minus 15 %% at speed and height.' % (install, A['inlet_recovery']))

    # ---- lattice lines, body moment, neutral point
    rows = lat['rows']
    mach_l = [r['mach'] for r in rows]
    li = lambda path, m: float(np.interp(m, mach_l, [_get(r, path) for r in rows]))
    r0 = rows[0]
    cla0, cma0 = r0['at_zero_lift']['CL']['alpha'], r0['at_zero_lift']['Cm']['alpha']
    lh = vl['horizontal_tail']['arm_m']
    cla_off = r0['tail_off']['cl_alpha']
    sh = vl['horizontal_tail']['area_m2']
    # downwash gradient at the tail from the lattice: tail lift per angle with the wing present against the free tail
    a_tail_free = 2 * math.pi * (PLAN['htail_span'] * FT) ** 2 / sh / (2 + math.sqrt(4 + ((PLAN['htail_span'] * FT) ** 2 / sh) ** 2 * (1 + math.tan(20 * DEG) ** 2)))
    deda = float(np.clip(1.0 - (cla0 - cla_off) * S / (sh * a_tail_free), 0.2, 0.7))
    cm_body = body_moment_slope(ref, cla_off, lh, deda)
    np_lattice = x_ref - cma0 / cla0 * c
    np_est = x_ref - (cma0 + cm_body) / cla0 * c
    np_tail_off_percent = (x_ref - (r0['tail_off']['cm_alpha'] + cm_body) / cla_off * c - ref['x_mac_le']) / c * 100
    fp = flow_points()
    flow = dict(points=[dict(alpha_deg=a, cl=cl, cd=cd, cm_quarter_chord=cm, converged=ok) for a, cl, cd, cm, ok in fp])
    if len(fp) >= 2:
        al = np.array([q[0] for q in fp]) * DEG
        clf, cmf = np.array([q[1] for q in fp]), np.array([q[3] for q in fp])
        claf, cmaf = float(np.polyfit(al, clf, 1)[0]), float(np.polyfit(al, cmf, 1)[0])
        local = [float(x_ref - (cmf[i + 1] - cmf[i]) / (clf[i + 1] - clf[i]) * c) for i in range(len(fp) - 1)]
        cdf = np.array([q[2] for q in fp])
        kf = float(np.polyfit(clf ** 2, cdf, 1)[0])
        flow.update(cl_alpha_per_rad=claf, cm_alpha_per_rad=cmaf, neutral_point_station_m=x_ref - cmaf / claf * c,
                    neutral_point_between_points_percent_mac=[(x - ref['x_mac_le']) / c * 100 for x in local],
                    cl_at_zero_alpha=float(np.interp(0.0, al, clf)), cm_at_zero_alpha=float(np.interp(0.0, al, cmf)),
                    drag_due_to_lift_factor=kf, cd_at_zero_alpha=float(np.interp(0.0, al, cdf)),
                    from_angles_deg=[q[0] for q in fp])
    # Flow runs made before 2026-11-15 (CL +0.118 and -0.286 at zero angle of attack, neutral point 12 % of the mean chord) are void: the body
    # mesh had wrongly turned triangles along the sharp edges and the solver took blocks of air behind the wing trailing edge for solid.
    # registry.orient_faces now repairs the orientation; the points read here are of the repaired body.
    flow['earlier_runs'] = dict(void=True, cl_at_zero_alpha=[0.1181, -0.2862], neutral_point_percent_mac=12,
                                note='Void: wrongly turned triangles in the flow-body mesh made the solver treat air behind the wing trailing edge as solid.')
    flow['used'] = 'current shape' if (USE_CURRENT_SHAPE_FLOW and 'cl_at_zero_alpha' in flow) else 'none'
    src = flow if flow['used'] == 'current shape' else dict(cl_at_zero_alpha=0.0, cm_at_zero_alpha=0.0, neutral_point_station_m=np_est)
    cl0, cm0 = src['cl_at_zero_alpha'], src['cm_at_zero_alpha']
    x_cg = np_est - A['static_margin'] * c
    z_cg = T['modelled_with_full_fuel_cg_m'][2]
    x_main = PLAN['main_gear_station'] * 0.01 * L
    x_nose = PLAN['nose_gear_station'] * 0.01 * L
    balance = dict(
        moment_reference_m=[x_ref, 0.0, 0.0],
        neutral_point=dict(lattice_no_body_m=np_lattice, body_shift_m=np_est - np_lattice, estimate_m=np_est,
                           estimate_percent_mac=(np_est - ref['x_mac_le']) / c * 100,
                           flow_solution_m=src.get('neutral_point_station_m'), flow_solution_percent_mac=(src['neutral_point_station_m'] - ref['x_mac_le']) / c * 100,
                           flow_solution_between_points_percent_mac=src.get('neutral_point_between_points_percent_mac'),
                           lattice_tail_off_with_body_percent_mac=np_tail_off_percent,
                           note='Two estimates. Used in the flight model: lattice of wing and tail plus the fuselage moment by the Multhopp strip method. '
                                'The flow solution of the whole aircraft (four angles, one grid) puts the neutral point further forward, and it moves aft with '
                                'angle of attack. The flight model assumes a static margin, not a place: the centre of gravity is set a fixed fraction of the '
                                'mean chord ahead of the estimate used, so with the flow-solution value the same flight behaviour needs the centre of gravity '
                                'that much further forward.'),
        cg_m=[x_cg, 0.0, z_cg], cg_percent_mac=(x_cg - ref['x_mac_le']) / c * 100,
        cg_rule='ASSUMPTION: %.0f %% of the mean chord ahead of the estimated neutral point, the same for every weight case' % (100 * A['static_margin']),
        modelled_items_cg_full_fuel_m=T['modelled_with_full_fuel_cg_m'][0], modelled_items_cg_no_fuel_m=T['modelled_without_fuel_cg_m'][0],
        main_gear_station_m=x_main, nose_gear_station_m=x_nose, nose_gear_load_fraction=(x_main - x_cg) / (x_main - x_nose),
        open_point='The items of the weight model (structure, engine, gear, fuel; no systems) balance at station %.1f ft with full fuel and the main wheels stand at %.1f ft, '
                   'both well aft of the flight centre of gravity assumed here (%.1f ft). Flown at the modelled balance the aircraft would be %.0f %% of the mean chord unstable '
                   'against the estimated neutral point. Either the real neutral point is further aft than this shape gives, or the real mass is further forward, or the real '
                   'aircraft flies unstable on its flight control system. Not resolved.'
                   % (T['modelled_with_full_fuel_cg_m'][0] / FT, x_main / FT, x_cg / FT, (T['modelled_with_full_fuel_cg_m'][0] - np_est) / c * 100))

    # ---- drag
    wet = G['wetted_area_m2'] if 'wetted_area_m2' in G else 77.09
    cd0 = A['cfe'] * wet / S
    cd_store = 2 * A['store_drag_area_ft2'] * FT2 / S
    cd_gear = A['gear_drag_area_ft2'] * FT2 / S
    ar = b * b / S
    tc = 0.5 * (PLAN['wing_tc_root'] + PLAN['wing_tc_tip']) / 100.0
    sweep_q = math.atan(math.tan(PLAN['wing_sweep'] * DEG) - 0.25 * (PLAN['wing_root_chord'] - PLAN['wing_tip_chord']) / (PLAN['wing_span'] / 2))
    bh = PLAN['htail_span'] * FT
    cl_de = r0['at_zero_lift']['CL']['elevator']
    cl_df = r0['at_zero_lift']['CL']['flap']
    flap_area_ratio = 0.53 * 0.85                    # flapped span share (27 to 80 % of the half span) times the chord there against the mean chord
    drag = dict(wetted_area_m2=wet, cd0_clean=cd0, cd_stores=cd_store, cd_gear=cd_gear, aspect_ratio=ar, k_full_suction=1.0 / (math.pi * ar),
                thickness_ratio_mean=tc, quarter_chord_sweep_deg=sweep_q / DEG,
                cd_flap_profile=A['flap_profile_drag'] * 0.24 ** 1.38 * flap_area_ratio,
                cd_tail_span_factor=S / (math.pi * bh * bh * 0.9), downwash_gradient=deda,
                source='Zero-lift drag: equivalent skin friction %.4f on the wetted area of the model (%.0f ft2, measured). Drag due to lift: 1 / (pi AR) with a leading-edge suction '
                       'schedule, the rest of the lift force tilted back by the angle of attack. Compressibility: Korn equation with Lock\'s fourth-power rise. Stores, gear, flap: '
                       'drag areas and the plain-flap profile drag rule as stated in ASSUME. The flow solution is not used for drag; it gives less zero-lift drag (%.4f against %.4f) '
                       'and about twice the drag due to lift (CD = CD0 + %.2f CL2 against about %.2f CL2 here), see the sensitivity in turn.md.'
                       % (A['cfe'], wet / FT2, src.get('cd_at_zero_alpha', float('nan')), cd0, src.get('drag_due_to_lift_factor', float('nan')),
                          A['suction_low'] / (math.pi * ar) + (1 - A['suction_low']) / cla0))

    out = dict(what='Flight statement of the Fury model (estimates)', statement=ASSUME_NOTE, assumptions=A,
               reference=dict(s_m2=S, b_m=b, c_m=c, x_mac_le_m=ref['x_mac_le'], length_m=L), planform=PLAN,
               weights=weights, engine=engine_d, balance=balance, drag=drag,
               lift=dict(cl_at_zero_alpha=cl0, cm_at_zero_alpha_quarter_chord=cm0, zero_alpha_source='flow solution (repaired body, 2026-11-15)' if src is flow else 'none: zero assumed',
                         cl_alpha_lattice={('%.1f' % m): li('at_zero_lift.CL.alpha', m) for m in MACHS}, cm_alpha_body_per_rad=cm_body,
                         cl_max={('%.2f' % m): cl_max(m) for m in (0.3, 0.5, 0.7, 0.8, 0.9)},
                         note='Lift slope from the lattice (wing and tail carried to the centreline). The flow solution gives a lower slope (%.2f against %.2f per rad at low speed): '
                              'if it is right, every angle of attack quoted for a given lift is about %.0f %% too small. Lift and pitching moment at zero angle of attack are taken '
                              'from the flow solution.' % (src.get('cl_alpha_per_rad', cla0), cla0, (cla0 / src.get('cl_alpha_per_rad', cla0) - 1) * 100)),
               flow_solution=flow, lattice_check=lat['check'])
    return out


def _get(d, path):
    for k in path.split('.'):
        d = d[k]
    return d


def cl_max(mach):
    return ASSUME['cl_max_low_speed'] * float(np.interp(mach, ASSUME['cl_max_mach'], ASSUME['cl_max_factor']))


_CACHE = {}


def statement():
    if 'st' not in _CACHE:
        f = OUT / 'aircraft.json'
        _CACHE['st'] = build()
    return _CACHE['st']


# ----------------------------------------------------------------------------------------------------------------------
# Coefficients at one Mach number
# ----------------------------------------------------------------------------------------------------------------------
class Aero:
    """Coefficient model at one Mach number: tables over angle of attack (about the quarter-chord point) and derivatives.
    stores: missiles on the pylons (drag only)."""

    def __init__(self, mach, stores=True, cl_max_delta=0.0, flow_polar=False):
        st = statement()
        A = ASSUME
        lat = lattice_table()
        rows = lat['rows']
        ml = [r['mach'] for r in rows]
        self.mach = mach
        g = lambda path: float(np.interp(mach, ml, [_get(r, path) for r in rows]))
        self.g = g
        self.st = st
        D = st['drag']
        self.S, self.b, self.c = st['reference']['s_m2'], st['reference']['b_m'], st['reference']['c_m']
        self.cla = g('at_zero_lift.CL.alpha')
        self.cma = g('at_zero_lift.Cm.alpha') + st['lift']['cm_alpha_body_per_rad']
        self.cl0, self.cm0 = st['lift']['cl_at_zero_alpha'], st['lift']['cm_at_zero_alpha_quarter_chord']
        self.cl_max = cl_max(mach) + cl_max_delta
        self.cd0 = D['cd0_clean'] + (D['cd_stores'] if stores else 0.0)
        self.k100 = D['k_full_suction']
        self.D = D
        self.suction_low, self.suction_at_clmax = A['suction_low'], A['suction_at_clmax']
        if flow_polar:
            # sensitivity case: zero-lift drag and drag due to lift as the flow solution gives them (CD = CD0 + K CL2, one suction value at every lift)
            F = st['flow_solution']
            self.cd0 = F['cd_at_zero_alpha'] + (D['cd_stores'] if stores else 0.0)
            sv = float(np.clip((1.0 / self.cla - F['drag_due_to_lift_factor']) / (1.0 / self.cla - self.k100), 0.0, 1.0))
            self.suction_low = self.suction_at_clmax = sv
        # Korn: drag-divergence Mach number of the wing at a lift coefficient
        self.cos_q = math.cos(D['quarter_chord_sweep_deg'] * DEG)
        w = A['stall_cap_width_deg']
        cla_deg = self.cla * DEG
        self.a_stall = (self.cl_max - self.cl0) / cla_deg + 0.5 * w
        self.a_line = self.a_stall - w
        self.alpha_lim = self.a_stall - A['limiter_margin_deg']

    # ---- lift, drag and moment at zero deflection
    def cl_of(self, a_deg):
        A = ASSUME
        cla, w = self.cla * DEG, A['stall_cap_width_deg']
        if a_deg <= self.a_line:
            return self.cl0 + cla * a_deg
        if a_deg <= self.a_stall:
            return self.cl_max - cla / (2.0 * w) * (self.a_stall - a_deg) ** 2
        return self.cl_max * (1.0 - A['post_stall_drop'] * min((a_deg - self.a_stall) / A['post_stall_over_deg'], 1.0))

    def cd_wave(self, cl):
        A = ASSUME
        mdd = A['korn_kappa'] / self.cos_q - self.D['thickness_ratio_mean'] / self.cos_q ** 2 - max(cl, 0.0) / (10.0 * self.cos_q ** 3) + A['drag_divergence_shift']
        mcrit = mdd - (0.1 / 80.0) ** (1.0 / 3.0)
        return 20.0 * max(self.mach - mcrit, 0.0) ** 4

    def cd_of(self, a_deg):
        A = ASSUME
        cl = self.cl_of(a_deg)
        s = self.suction_low - (self.suction_low - self.suction_at_clmax) * float(np.clip((abs(cl) / self.cl_max - A['suction_break']) / (1.0 - A['suction_break']), 0.0, 1.0))
        k = s * self.k100 + (1.0 - s) / self.cla
        polar = self.cd0 + k * cl * cl + self.cd_wave(cl)
        plate = cl * math.tan(a_deg * DEG)
        blend = float(np.clip((a_deg - self.a_stall) / A['drag_rise_over_deg'], 0.0, 1.0))
        return polar + blend * max(plate - polar, 0.0)

    def cm_of(self, a_deg):
        return self.cm0 + self.cma * a_deg * DEG

    def knots(self):
        s = self.a_stall
        w = ASSUME['stall_cap_width_deg']
        return [-8.0, -4.0, 0.0, 0.5 * self.a_line, self.a_line, s - 0.75 * w, s - 0.5 * w, s - 0.25 * w, s, s + 2.0, s + 4.0, s + 6.0, s + 12.0, max(s + 24.0, 45.0)]

    def table(self):
        kn = self.knots()
        return dict(alpha_deg=kn, cl=[self.cl_of(a) for a in kn], cd=[self.cd_of(a) for a in kn], cm=[self.cm_of(a) for a in kn], knots_deg=kn,
                    alpha_cl_max_deg=self.a_stall, cl_max=self.cl_max, line_ends_deg=self.a_line, polar_fit_deg=[-8.0, self.a_line],
                    alpha_lim_deg=self.alpha_lim, alpha_min_deg=-6.0)

    # ---- derivatives (per rad; lateral ones as a + b CL or a + b CL^2 from the lattice at zero lift and at 0.1 rad)
    def derivatives(self):
        A, g, D = ASSUME, self.g, self.D
        clr = g('cl_at_alpha_0p1')
        z = lambda p: g('at_zero_lift.' + p)
        lin = lambda p: (z(p), (g('at_alpha_0p1.' + p) - z(p)) / clr)
        sq = lambda p: (z(p), (g('at_alpha_0p1.' + p) - z(p)) / clr ** 2)
        st = self.st
        vol = 0.80 * st['balance'].get('volume_m3', 8.4)
        ef = A['fin_efficiency']
        cy_b_body = -2.0 * 1.2 * (1.25 / self.S)                                          # Roskam: -2 K (S0 / S), K 1.2, S0 the largest fuselage cross-section (about 13.5 ft2)
        cn_b_body = -1.3 * vol / (self.S * self.b) * 0.75                                 # Raymer eq. 16.47: -1.3 (volume / S b) (depth / width)
        cll_b0, cll_b1 = lin('Cl.beta'); cll_r0, cll_r1 = lin('Cl.rh'); cn_p0, cn_p1 = lin('Cn.ph')
        cn_b0, cn_b1 = sq('Cn.beta'); cn_r0, cn_r1 = sq('Cn.rh')
        cl_de, cm_de = z('CL.elevator'), z('Cm.elevator')
        cl_df, cm_df = z('CL.flap'), z('Cm.flap')
        k1 = self.k100 * 1.15
        return dict(
            cl_q=z('CL.qh'), cm_q=z('Cm.qh'),
            cl_de=cl_de, cm_de=cm_de, cl_df=cl_df, cm_df=cm_df,
            # drag of the deflected surfaces: tail lift in the downwash of the wing and its own induced drag; flap lift on the wing polar; profile drag with sin2
            cd_de1=cl_de * D['downwash_gradient'] / self.cla, cd_de3=cl_de ** 2 * D['cd_tail_span_factor'], cd_de2=0.02,
            cd_df1=2.0 * k1 * cl_df, cd_df3=k1 * cl_df ** 2, cd_df2=D['cd_flap_profile'], cd_dr2=0.02,
            cd_gear=D['cd_gear'], cm_gear=-D['cd_gear'] * 0.95 / self.c,                     # the gear drag acts about 0.95 m below the centre of gravity
            cy_b=ef * z('CY.beta') + cy_b_body, cy_p=z('CY.ph'), cy_r=z('CY.rh'), cy_da=z('CY.aileron'), cy_dr=A['rudder_k'] * z('CY.rudder'),
            cll_b0=cll_b0, cll_b1=cll_b1, cll_p=z('Cl.ph'), cll_r0=cll_r0, cll_r1=cll_r1, cll_da=z('Cl.aileron'), cll_dr=A['rudder_k'] * z('Cl.rudder'),
            cn_b0=ef * cn_b0 + cn_b_body, cn_b1=cn_b1, cn_p0=cn_p0, cn_p1=cn_p1, cn_r0=cn_r0, cn_r1=cn_r1, cn_da=z('Cn.aileron'), cn_dr=A['rudder_k'] * z('Cn.rudder'),
            stab_k1=A['stab_k1'], stab_k2=A['stab_k2'], stab_break=A['stab_break_deg'] * DEG,
            flap_k1=A['flap_k1'], flap_k2=A['flap_k2'], flap_break=A['flap_break_deg'] * DEG,
            body=dict(cy_b=cy_b_body, cn_b=cn_b_body))


# ----------------------------------------------------------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------------------------------------------------------
def thrust_max(mach, alt_m, factor=1.0):
    """Installed maximum thrust, N."""
    A = ASSUME
    st = statement()
    at = isa(alt_m)
    ram = 1 + 0.2 * mach * mach
    d0, t0 = at['p_ratio'] * ram ** 3.5, at['t_ratio'] * ram
    a = d0 * (1 - A['lapse_k_mach'] * math.sqrt(max(mach, 0.0)) - 3.0 * max(t0 - A['throttle_ratio'], 0.0) / (1.5 + mach))
    return max(a, 0.0) * st['engine']['thrust_installed_sl_static_N'] * factor


# ----------------------------------------------------------------------------------------------------------------------
# Aircraft object for ref/perf.py (trimmed point performance)
# ----------------------------------------------------------------------------------------------------------------------
class Fury:
    def __init__(self, case='combat', weight_lb=None, thrust_factor=1.0, drag_factor=1.0, cl_max_delta=0.0, stores=True, gear=0.0, flap_deg=0.0, flow_polar=False):
        st = statement()
        self.st = st
        self.case = case
        w = st['weights']['cases'][case]['weight_lb'] if weight_lb is None else weight_lb
        self.weight_lb = w
        self.weight_N = w * LB * G0
        self.s_ref_m2 = st['reference']['s_m2']
        self.n_limit = ASSUME['n_limit']
        self.cl_scan_max = 1.9
        self.thrust_factor, self.drag_factor, self.cl_max_delta = thrust_factor, drag_factor, cl_max_delta
        self.stores, self.gear, self.flap = stores, gear, flap_deg * DEG
        self.flow_polar = flow_polar
        self.name = 'Fury model, %s (%.0f lb)' % (st['weights']['cases'][case]['label'] if weight_lb is None else 'weight set', w)
        self._aero = {}
        self.dx = (st['balance']['cg_m'][0] - st['balance']['moment_reference_m'][0]) / st['reference']['c_m']
        self.ze = st['engine']['thrust_line_z_m'] - st['balance']['cg_m'][2]

    def thrust(self, mach, alt_m):
        return thrust_max(mach, alt_m, self.thrust_factor)

    def aero(self, mach):
        k = round(mach, 4)
        if k not in self._aero:
            a = Aero(mach, self.stores, self.cl_max_delta, self.flow_polar)
            self._aero[k] = (a, a.derivatives())
        return self._aero[k]

    def flap_eff(self, d):
        A = ASSUME
        return A['flap_k1'] * d - A['flap_k2'] * math.copysign(max(abs(d) - A['flap_break_deg'] * DEG, 0.0), d)

    def stab_eff(self, d):
        A = ASSUME
        return A['stab_k1'] * d - A['stab_k2'] * math.copysign(max(abs(d) - A['stab_break_deg'] * DEG, 0.0), d)

    def trimmed(self, a_deg, mach, alt_m, thrust_fraction=1.0):
        """Trimmed lift and drag at an angle of attack: stabilator for zero pitching moment about the centre of gravity (steady, no pitch rate)."""
        A = ASSUME
        a, dv = self.aero(mach)
        at = isa(alt_m)
        q = 0.5 * at['rho'] * (mach * at['a']) ** 2
        fe = self.flap_eff(self.flap)
        clw = a.cl_of(a_deg)
        cm_fixed = a.cm_of(a_deg) + dv['cm_df'] * fe + dv['cm_gear'] * self.gear - self.ze * self.thrust(mach, alt_m) * thrust_fraction / (q * a.S * a.c)
        cl_fixed = clw + dv['cl_df'] * fe
        # moment about the centre of gravity: Cm_ref + dx (CL cos a + CD sin a) ~ Cm_ref + dx CL; solve the stabilator (effective deflection)
        de_eff = -(cm_fixed + self.dx * cl_fixed) / (dv['cm_de'] + self.dx * dv['cl_de'])
        # effective -> real deflection
        k1, k2, br = A['stab_k1'], A['stab_k2'], A['stab_break_deg'] * DEG
        de = de_eff / k1 if abs(de_eff) <= k1 * br else math.copysign(br + (abs(de_eff) - k1 * br) / (k1 - k2), de_eff)
        cl = cl_fixed + dv['cl_de'] * de_eff
        cd = (a.cd_of(a_deg) + (dv['cd_de1'] * clw) * de_eff + dv['cd_de3'] * de_eff ** 2 + dv['cd_de2'] * math.sin(de) ** 2
              + dv['cd_df1'] * clw * fe + dv['cd_df3'] * fe * fe + dv['cd_df2'] * math.sin(self.flap) ** 2 + dv['cd_gear'] * self.gear) * self.drag_factor
        return cl, cd, de

    def state(self, cl, mach, alt_m):
        a, dv = self.aero(mach)
        key = ('pol', round(mach, 4), round(alt_m, 1))
        if key not in self._aero:
            al = np.linspace(-4.0, a.alpha_lim, 140)
            pts = [self.trimmed(x, mach, alt_m) for x in al]
            self._aero[key] = (al, np.array([p[0] for p in pts]), np.array([p[1] for p in pts]), np.array([p[2] for p in pts]))
        al, clt, cdt, det = self._aero[key]
        lo, hi = ASSUME['stabilator_deg']
        if cl > clt[-1]:
            return dict(ok=False, why='lift (angle-of-attack limiter %.1f deg, trimmed CL %.2f)' % (a.alpha_lim, clt[-1]))
        alpha = float(np.interp(cl, clt, al))
        de = float(np.interp(cl, clt, det))
        if not (lo * DEG <= de <= hi * DEG):
            return dict(ok=False, why='stabilator travel')
        return dict(ok=True, cd=float(np.interp(cl, clt, cdt)), alpha_rad=alpha * DEG, delta_deg=de / DEG)


# ----------------------------------------------------------------------------------------------------------------------
def write():
    OUT.mkdir(exist_ok=True)
    st = build()
    _CACHE['st'] = st
    (OUT / 'aircraft.json').write_text(json.dumps(st, indent=1))
    W, B, E, R = st['weights'], st['balance'], st['engine'], st['reference']
    npn = B['neutral_point']
    md = ['# Flight statement of the Fury model (estimates)', '',
          'Everything here is an estimate from the shape of this model and public figures. No weight, thrust curve or aerodynamic coefficient of the real aircraft is published.', '',
          '## Weights', '', '| Item | Weight [lb] | Basis |', '|---|---:|---|',
          '| Structure | %.0f | %s |' % (W['structure_lb'], W['structure_note']),
          '| Engine and jet pipe | %.0f | %s |' % (W['engine_lb'], W['engine_note']),
          '| Landing gear | %.0f | weight model of the gear (analysis/results/mass.json) |' % W['landing_gear_lb'],
          '| Systems | %.0f | assumption |' % W['systems_lb'], '| Mission systems | %.0f | assumption |' % W['mission_systems_lb'],
          '| **Empty** | **%.0f** | |' % W['empty_lb'], '| Usable fuel, full | %.0f | %s |' % (W['usable_fuel_lb'], W['fuel_note']),
          '| Stores | %.0f | %s |' % (W['stores_lb'], W['stores_note']), '',
          '| Case | Weight [lb] | Wing loading [lb/ft2] | Static thrust / weight | Ixx, Iyy, Izz [slug ft2] |', '|---|---:|---:|---:|---|']
    for k, cse in W['cases'].items():
        i = cse['inertia']
        md.append('| %s (%s) | %.0f | %.1f | %.2f | %.0f, %.0f, %.0f |' % (k, cse['label'], cse['weight_lb'], cse['wing_loading_lb_ft2'],
                                                                         E['thrust_installed_sl_static_N'] / LBF / cse['weight_lb'], i['ixx'] / SLUG_FT2, i['iyy'] / SLUG_FT2, i['izz'] / SLUG_FT2))
    md += ['', W['statement'], '', '## Reference and balance', '',
           'Wing area %.1f ft2, span %.2f ft, mean aerodynamic chord %.2f ft with its leading edge at station %.2f ft.' % (R['s_m2'] / FT2, R['b_m'] / FT, R['c_m'] / FT, R['x_mac_le_m'] / FT), '',
           '| Point | Station [ft] | % of the mean chord |', '|---|---:|---:|',
           '| Neutral point, lattice of wing and tail (no body) | %.2f | %.0f |' % (npn['lattice_no_body_m'] / FT, (npn['lattice_no_body_m'] - R['x_mac_le_m']) / R['c_m'] * 100),
           '| Neutral point with the fuselage moment (used) | %.2f | %.0f |' % (npn['estimate_m'] / FT, npn['estimate_percent_mac']),
           '| Neutral point of the flow solution (line through all angles) | %.2f | %.0f |' % (npn['flow_solution_m'] / FT, npn['flow_solution_percent_mac']),
           '| Centre of gravity flown (assumed) | %.2f | %.0f |' % (B['cg_m'][0] / FT, B['cg_percent_mac']),
           '| Weight-model items, full fuel | %.2f | %.0f |' % (B['modelled_items_cg_full_fuel_m'] / FT, (B['modelled_items_cg_full_fuel_m'] - R['x_mac_le_m']) / R['c_m'] * 100),
           '| Main wheels | %.2f | |' % (B['main_gear_station_m'] / FT), '', npn['note'], '', B['open_point'], '',
           '## Engine', '', E['source'], '',
           '| Mach | Sea level [lbf] | 15,000 ft [lbf] | 30,000 ft [lbf] |', '|---:|---:|---:|---:|']
    for m in (0.0, 0.2, 0.4, 0.6, 0.8, 0.9):
        md.append('| %.1f | %.0f | %.0f | %.0f |' % (m, thrust_max(m, 0) / LBF, thrust_max(m, 15000 * FT) / LBF, thrust_max(m, 30000 * FT) / LBF))
    md += ['', '## Lift and drag (clean, with the two missiles)', '', st['drag']['source'], '',
           '| Mach | Lift slope [per deg] | Usable CLmax | Angle of the limiter [deg] | Zero-lift drag | Best lift/drag (trimmed) |', '|---:|---:|---:|---:|---:|---:|']
    ac = Fury('combat')
    for m in (0.3, 0.5, 0.7, 0.8, 0.9):
        a, dv = ac.aero(m)
        ld = max(cl / cd for cl, cd, _ in (ac.trimmed(x, m, 4572.0) for x in np.linspace(0, 10, 60)))
        md.append('| %.1f | %.4f | %.2f | %.1f | %.4f | %.1f |' % (m, a.cla * DEG, a.cl_max, a.alpha_lim, a.cd0 + a.cd_wave(0.0), ld))
    a, dv = ac.aero(0.5)
    md += ['', '## Derivatives at Mach 0.5 (per rad, lattice with the stated factors)', '',
           '| | Value | | Value |', '|---|---:|---|---:|']
    keys = [k for k in dv if k != 'body' and not isinstance(dv[k], dict)]
    for k1, k2 in zip(keys[0::2], keys[1::2] + ['']):
        md.append('| %s | %.4f | %s | %s |' % (k1, dv[k1], k2, ('%.4f' % dv[k2]) if k2 else ''))
    (OUT / 'aircraft.md').write_text('\n'.join(md), encoding='utf-8')
    return st


if __name__ == '__main__':
    st = write()
    print((OUT / 'aircraft.md').read_text(encoding='utf-8'))
