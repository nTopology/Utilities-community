"""Engine models: small-turbofan catalogue, the selected engine, thrust lapse and fuel-flow models,
and the F110-GE-129 model of the F-16 reference. Numpy only.

PUBLIC FIGURES AND ESTIMATES. None of this is manufacturer installed-performance data. Each entry names its source;
values marked "estimate" were made here. Thrust is sea-level static, uninstalled.

Method: a catalogue of real engines plus the Mattingly lapse forms.
"""
from __future__ import annotations
import json
import math
import os
import numpy as np
from common import LBF, LB, IN, isa, FT

# ------------------------------------------------------------------------------------------------------------------
# catalogue: real small turbofans, public figures
# ------------------------------------------------------------------------------------------------------------------
CATALOGUE = [
    dict(name='Williams FJ33-5A', thrust_sl_static_N=1846 * LBF, mass_kg=319 * LB, length_m=38.43 * IN, max_diameter_m=18.36 * IN,
         bypass_ratio=None, tsfc_static_per_h=0.486,
         source='Wikipedia "Williams FJ33" (read 2026-11-13): 1,846 lbf, 38.43 in long, 18.36 in diameter, 0.486 lb/(lbf h) static, dry weight '
                '"less than 300 lb". Mass used here: 319 lb, the Williams International FJ33 brochure figure given by the lead (not re-read by SIZE); '
                'the two public figures differ by about 20 lb. Engine of the Kratos XQ-58A per the Wikipedia page (the variant is not stated).'),
    dict(name='Williams FJ44-3AP', thrust_sl_static_N=3000 * LBF, mass_kg=535 * LB, length_m=48.0 * IN, max_diameter_m=23.0 * IN,
         bypass_ratio=None, tsfc_static_per_h=None,
         source='Wikipedia "Williams FJ44" type-certificate table (read 2026-11-13): FJ44-3 3,000 lbf, 516 to 535 lb, 48.0 in, 23.0 in.'),
    dict(name='Williams FJ44-4M', thrust_sl_static_N=3790 * LBF, mass_kg=658 * LB, length_m=52.8 * IN, max_diameter_m=25.3 * IN,
         bypass_ratio=None, tsfc_static_per_h=None,
         source='Thrust 3,790 lbf: public Aero L-39NG figures for its FJ44-4M (airrecognition.com and Wikipedia "Aero L-39NG", read 2026-11-13; '
                'one source, key.aero, gives 3,600 lbf). Mass, length and diameter: Wikipedia "Williams FJ44" type-certificate table for the '
                'FJ44-4 (3,600 lbf, 658 lb, 52.8 in long, 25.3 in diameter). The same page lists the FJ44-4M for the Aero L-39 Skyfox and the '
                'Anduril YFQ-44, and the FJ44-4 for the Boeing MQ-28.'),
]
BY_NAME = {e['name']: e for e in CATALOGUE}
SELECTED = 'Williams FJ33-5A'          # lead decision of revision 3: the engine that fits the concept's own engine bay, inlet and exhaust
ALTERNATIVE = 'Williams FJ44-4M'       # kept only as a labelled sensitivity: the bigger engine that does not fit the concept's bay
ALTERNATIVE_NOTE = ('SENSITIVITY ONLY. The FJ44-4M was the revision 2 choice; it needed a new inlet with a hump and a moved engine and was rejected. '
                    'It does not fit the design. Thrust and engine weight are changed, balance, duct and bay are not redone.')

# estimates for the selected engine (not published in the sources read). The geometry values are the lead's, in model/design.py ENGINE.
SELECTED_ESTIMATES = dict(
    bypass_ratio=None,
    bypass_ratio_note='not in the sources read. Wikipedia mirrors give 3.28 for the FJ44-1A, the engine the FJ33 was scaled down from; the lapse and '
                      'fuel-flow forms below assume a bypass ratio of 3 to 4.',
    fan_face_diameter_m=0.434,
    fan_face_note="ESTIMATE of the lead (model/design.py ENGINE r_face = 0.217 m): the fan tip diameter is not published; 0.933 of the 18.36 in "
                  "envelope. The concept's own face is 14 in (0.356 m), which would choke at this engine's estimated flow.",
    hub_tip_ratio=0.40,
    specific_thrust_lbf_per_lb_s=34.0,
    mass_flow_sls_kg_s=24.6,
    mass_flow_note='ESTIMATE. Mass flow is not published. Sea-level static flow = thrust / specific thrust = 1,846 lbf / 34 lbf per lb/s = 54.3 lb/s '
                   '(24.6 kg/s); 34 is assumed for a bypass ratio of 3 to 4 (the FJ44-1A public figures, 1,900 lbf and about 63 lb/s, give 30). '
                   'On the estimated annulus (0.124 m2) the fan-face Mach number is 0.58. Uncertainty about 15 %.',
    aft_diameter_m=0.38,
    aft_diameter_note='ESTIMATE of the lead (model/design.py ENGINE r_aft = 0.19 m): aft case and mixer.',
    cg_fraction_of_length=0.42,
)


def _duct():
    """Inlet duct numbers of the lead's ORCA model (model/out/W4/duct.json): areas measured in ORCA, Mach numbers and loss estimated from them."""
    p = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'out', 'W4', 'duct.json'))
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        return dict(source='model/out/W4/duct.json (lead, areas measured in ORCA; loss estimated)', read=True,
                    recovery=float(d['pressure_loss']['recovery_estimate']), throat_area_m2=float(d['areas']['throat_area']),
                    face_area_m2=float(d['areas']['face_area']), area_ratio_face_over_throat=float(d['areas']['area_ratio_face_over_throat']),
                    throat_mach_full_flow=float(d['pressure_loss']['throat_mach']), length_m=float(d['guide_curve']['length_m']),
                    start_x_m=float(d['start_x_m']), lip_station_x_m=float(d['lip_station_x_m']), exit_area_m2=float(d['exhaust']['exit_area_m2']),
                    exit_area_note=d['exhaust'].get('note'), loss_note=d['pressure_loss'].get('note'))
    except Exception as ex:                      # the file is the lead's; without it the values of 2026-11-13 10:32 are used and that is said
        return dict(source='model/out/W4/duct.json could not be read (%s); values of the file of 2026-11-13 10:32 are used' % type(ex).__name__, read=False,
                    recovery=0.9718, throat_area_m2=0.12491, face_area_m2=0.14794, area_ratio_face_over_throat=1.184, throat_mach_full_flow=0.571,
                    length_m=3.018, start_x_m=1.591, lip_station_x_m=2.390, exit_area_m2=0.07457, exit_area_note=None, loss_note=None)


DUCT = _duct()
INSTALL = dict(
    recovery=DUCT['recovery'], ram_recovery_factor=1.35, offtake_factor=0.985, nozzle_factor=0.98,
    form='installed / uninstalled thrust = (1 - 1.35 (1 - recovery)) x 0.985 x 0.98',
    note='Recovery from the measured duct (' + DUCT['source'] + '): estimated from the measured areas, length and offset at a throat Mach number of %.2f, '
         'full flow. 1.35 %% of thrust per 1 %% of recovery: Raymer, Aircraft Design, installed thrust correction for subsonic inlets. 0.985: ASSUMPTION for the '
         'generator and hydraulic power offtake, no bleed. 0.98: ASSUMPTION for the flat serrated nozzle and its 1.1 m transition pipe against a round nozzle. '
         'Not included: loss and distortion of the dorsal inlet at high angle of attack, where it sits in the forebody wake (the lead does not analyse it either), '
         'and any flow restriction from the nozzle exit area.' % DUCT['throat_mach_full_flow'],
    replaces='revision 2 assumed 0.93 outright with a recovery of 0.96 to 0.97; the product is now built from the duct file',
    revision_3_install_factor=0.9285,
    revision_4='the duct file was rewritten for the chevron hood of the upper lip (CONTRACT decision 15): throat 188.3 in2 against 193.6 in2, throat Mach number '
               '0.60 at the estimated full flow (the limit the lead set; no margin), recovery estimate 0.970 against 0.972. The factor follows the file: 0.9256 against 0.9285.')
INSTALL['install_factor'] = round((1 - INSTALL['ram_recovery_factor'] * (1 - INSTALL['recovery'])) * INSTALL['offtake_factor'] * INSTALL['nozzle_factor'], 4)

# ------------------------------------------------------------------------------------------------------------------
# thrust and fuel flow of the UAS engine
# ------------------------------------------------------------------------------------------------------------------
LAPSE = dict(
    form='T / T_sl_static = d0 * (1 - k sqrt(M)) for t0 <= TR, minus 3 (t0 - TR) / (1.5 + M) above; d0 = (p/p0)(1 + 0.2 M^2)^3.5, t0 = (T/T0)(1 + 0.2 M^2)',
    k_mach=0.30, throttle_ratio=1.04,
    source='Mattingly, Heiser and Pratt, Aircraft Engine Design, high-bypass turbofan form (their k = 0.49 for bypass ratios near 8; their '
           'low-bypass form has no Mach term). k = 0.30 is an ASSUMPTION for a bypass ratio of 3 to 4. One rough public anchor, for the larger FJ44-4A '
           'of the same family (none was found for the FJ33): a Citation CJ4 cruising near Mach 0.77 at 41,000 ft needs about 0.19 of static thrust per '
           'engine if its lift-to-drag ratio is 11; the form gives 0.192. Throttle ratio 1.04: flat rating to about ISA + 11 C (assumption).',
    uncertainty='plus or minus 15 % on thrust at altitude and speed (stated, not measured). Turn results are rerun with thrust x 0.85 and x 1.15.',
    install_factor=INSTALL['install_factor'],
    install_note=INSTALL['form'] + ' = %.3f, applied to thrust at every condition. ' % INSTALL['install_factor'] + INSTALL['note'],
)
TSFC = dict(
    form='TSFC [lb/(lbf h)] = (c0 + c1 M) sqrt(T/T0) * installation',
    c0=0.486, c1=0.50, installation=1.05,
    source='Static value 0.486 lb/(lbf h): the public figure of the FJ33 (Wikipedia). Growth with Mach number: Mattingly high-bypass form '
           '(0.45 + 0.54 M) sqrt(theta), slope taken as 0.50 (ASSUMPTION). Installation 1.05 (ASSUMPTION: recovery, offtake, nozzle). ASSUMPTION for '
           'part power: TSFC is held at the full-power value (optimistic by a few percent at low power settings).',
    uncertainty='plus or minus 10 %',
)


def _d0t0(mach, alt_m):
    at = isa(alt_m)
    return at['p_ratio'] * (1 + 0.2 * mach * mach) ** 3.5, at['t_ratio'] * (1 + 0.2 * mach * mach), at


def lapse_turbofan(mach, alt_m, k=None, tr=None):
    """Maximum thrust / sea-level static thrust of the UAS turbofan (uninstalled shape)."""
    k = LAPSE['k_mach'] if k is None else k
    tr = LAPSE['throttle_ratio'] if tr is None else tr
    d0, t0, _ = _d0t0(mach, alt_m)
    a = d0 * (1 - k * math.sqrt(max(mach, 0.0)))
    if t0 > tr:
        a -= d0 * 3 * (t0 - tr) / (1.5 + mach)
    return max(a, 0.0)


def thrust_uas(mach, alt_m, thrust_sl_static_N, factor=1.0):
    """Installed maximum thrust of the UAS engine, N."""
    return thrust_sl_static_N * LAPSE['install_factor'] * lapse_turbofan(mach, alt_m) * factor


def tsfc_uas_per_s(mach, alt_m):
    """Installed thrust specific fuel consumption in kg/(N s)."""
    at = isa(alt_m)
    lb_per_lbf_h = (TSFC['c0'] + TSFC['c1'] * mach) * math.sqrt(at['t_ratio']) * TSFC['installation']
    return lb_per_lbf_h / 3600.0 / 9.80665


def corrected_flow_per_area(mach_face):
    """kg/s per m2 of flow area at sea-level standard total conditions."""
    return 101325.0 * math.sqrt(1.4 / (287.053 * 288.15)) * mach_face * (1 + 0.2 * mach_face ** 2) ** -3.0


def mass_flow(e, mach, alt_m, recovery=None):
    """Engine mass flow in kg/s at full corrected flow: W = Wc * (pt2/p0) / sqrt(Tt2/T0). ESTIMATE. Recovery from the duct file unless given."""
    recovery = DUCT['recovery'] if recovery is None else recovery
    wc = (e['thrust_sl_static_N'] / LBF) / SELECTED_ESTIMATES['specific_thrust_lbf_per_lb_s'] * LB
    d0, t0, _ = _d0t0(mach, alt_m)
    rec = 1.0 if mach < 0.05 else recovery
    return wc * d0 * rec / math.sqrt(t0), wc


# ------------------------------------------------------------------------------------------------------------------
# F110-GE-129 of the F-16C Block 50: public table shape, scaled to the public ratings
# ------------------------------------------------------------------------------------------------------------------
F110 = dict(
    name='General Electric F110-GE-129',
    thrust_max_ab_sl_static_N=29500 * LBF, thrust_mil_sl_static_N=17155 * LBF,
    source='Public ratings: 29,500 lbf class with afterburner (other public sources give 28,984 and 29,588 lbf), 17,155 lbf military power.',
    table_source='Shape with Mach and altitude: NASA TP-1538 (Nguyen et al., 1979), Table VI(b), installed thrust of the F-16A engine model '
                 '(F100-PW-200 class); the Mach 0 row is from the Stevens and Lewis '
                 'port (AeroBenchVVPython thrust.py).',
    scaling='ESTIMATE: every table value is multiplied by the ratio of public uninstalled ratings, F110-GE-129 over F100-PW-200 '
            '(afterburner 29,500 / 23,830 = 1.238; military 17,155 / 14,670 = 1.169). The F110 does not lapse exactly like the F100; '
            'uncertainty about plus or minus 10 %. Turn results are rerun with thrust x 0.9 and x 1.1.',
    scale_ab=29500.0 / 23830.0, scale_mil=17155.0 / 14670.0,
    mach=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    altitude_ft=[0, 10000, 20000, 30000, 40000, 50000],
    military_lbf=[[12680, 9150, 6200, 3950, 2450, 1400], [12680, 9150, 6313, 4040, 2470, 1400], [12610, 9312, 6610, 4290, 2600, 1560],
                  [12640, 9839, 7090, 4660, 2840, 1660], [12390, 10176, 7750, 5320, 3250, 1930], [11680, 9848, 8050, 6100, 3800, 2310]],
    maximum_lbf=[[20000, 15000, 10800, 7000, 4000, 2500], [21420, 15700, 11225, 7323, 4435, 2600], [22700, 16860, 12250, 8154, 5000, 2835],
                 [24240, 18910, 13760, 9285, 5700, 3215], [26070, 21075, 15975, 11115, 6860, 3950], [28886, 23319, 18300, 13484, 8642, 5057]],
)


def thrust_f16(mach, alt_m, power='ab', factor=1.0):
    """Installed thrust of the F-16C Block 50 model in N: bilinear in Mach and altitude on the scaled table (held at the table edges)."""
    tab = np.array(F110['maximum_lbf' if power == 'ab' else 'military_lbf'], float)
    sc = F110['scale_ab' if power == 'ab' else 'scale_mil']
    m = np.clip(mach, 0.0, 1.0)
    h = np.clip(alt_m / FT, 0.0, 50000.0)
    col = np.array([np.interp(h, F110['altitude_ft'], row) for row in tab])
    return float(np.interp(m, F110['mach'], col)) * sc * LBF * factor


if __name__ == '__main__':
    e = BY_NAME[SELECTED]
    print(SELECTED, 'install factor', LAPSE['install_factor'], DUCT)
    for (m, hft) in ((0, 0), (0.3, 0), (0.3, 15000), (0.5, 15000), (0.7, 15000), (0.8, 30000), (0.77, 41000)):
        w, wc = mass_flow(e, m, hft * FT)
        print('M %.2f %6d ft  lapse %.3f  T %.0f lbf  tsfc %.3f /h  W %.1f kg/s' % (m, hft, lapse_turbofan(m, hft * FT), thrust_uas(m, hft * FT, e['thrust_sl_static_N']) / LBF,
                                                                                    tsfc_uas_per_s(m, hft * FT) * 3600 * 9.80665, w))
    print('F-16 AB SL M0.7 %.0f  15k M0.5 %.0f  mil %.0f' % (thrust_f16(0.7, 0) / LBF, thrust_f16(0.5, 15000 * FT) / LBF, thrust_f16(0.5, 15000 * FT, 'mil') / LBF))
