"""F-16C Block 50 reference for the turn comparison: a point-performance model built from PUBLIC data.

THIS IS AN ESTIMATE FROM PUBLIC DATA. It is not flight manual data and not manufacturer data. Sources are named in
each block. Running this file writes study/f16_reference.json with the model, its check against published sustained
turn figures and the mismatch.

    python f16_model.py
"""
from __future__ import annotations
import json
import math
import os
import time
import numpy as np
import engines
import perf
from common import FT, FT2, LB, LBF, KT, G0, isa

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- low-speed aerodynamic tables (body axes, S = 300 ft2, moments about 0.35 MAC):
# the reduced F-16 model of Stevens and Lewis ("Aircraft Control and Simulation",
# Appendix A) as ported in AeroBenchVVPython (public release 88ABW-2020-2188), itself from NASA TP-1538 (Nguyen et al., 1979).
ALPHA = [-10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45]
ELEV = [-24, -12, 0, 12, 24]
CX = [[-0.099, -0.081, -0.081, -0.063, -0.025, 0.044, 0.097, 0.113, 0.145, 0.167, 0.174, 0.166],
      [-0.048, -0.038, -0.04, -0.021, 0.016, 0.083, 0.127, 0.137, 0.162, 0.177, 0.179, 0.167],
      [-0.022, -0.02, -0.021, -0.004, 0.032, 0.094, 0.128, 0.13, 0.154, 0.161, 0.155, 0.138],
      [-0.04, -0.038, -0.039, -0.025, 0.006, 0.062, 0.087, 0.085, 0.1, 0.11, 0.104, 0.091],
      [-0.083, -0.073, -0.076, -0.072, -0.046, 0.012, 0.024, 0.025, 0.043, 0.053, 0.047, 0.04]]
CZ_ALPHA = [0.77, 0.241, -0.1, -0.415, -0.731, -1.053, -1.355, -1.646, -1.917, -2.12, -2.248, -2.229]
CM = [[0.205, 0.168, 0.186, 0.196, 0.213, 0.251, 0.245, 0.238, 0.252, 0.231, 0.198, 0.192],
      [0.081, 0.077, 0.107, 0.11, 0.11, 0.141, 0.127, 0.119, 0.133, 0.108, 0.081, 0.093],
      [-0.046, -0.02, -0.009, -0.005, -0.006, 0.01, 0.006, -0.001, 0.014, 0.0, -0.013, 0.032],
      [-0.174, -0.145, -0.121, -0.127, -0.129, -0.102, -0.097, -0.113, -0.087, -0.084, -0.069, -0.006],
      [-0.259, -0.202, -0.184, -0.193, -0.199, -0.15, -0.16, -0.167, -0.104, -0.076, -0.041, -0.005]]

MODEL = dict(
    statement='ESTIMATE FROM PUBLIC DATA. Not flight manual data, not manufacturer data.',
    aircraft='F-16C Block 50, F110-GE-129, 50 % internal fuel, two AIM-9 on the wing tips (CONTRACT decision 6)',
    weights=dict(
        without_fuel_lb=19700, internal_fuel_lb=7000, fuel_fraction_carried=0.5, missiles_lb=2 * 190, weight_lb=19700 + 3500 + 380,
        source='USAF and Air National Guard F-16 fact sheets as returned by a web search on 2026-11-13 (search summary, the pages were not opened): "19,700 pounds without fuel", '
               '"7,000 pounds internal" fuel. Other public listings give 18,900 lb empty for a Block 50; the higher figure is used because the fact-sheet weight includes the pilot, '
               'gun and fluids. AIM-9: about 190 lb each (public figure, from memory). Uncertainty of the flight weight about plus or minus 800 lb.'),
    wing=dict(area_ft2=300.0, span_ft=30.0, mac_ft=11.32, aspect_ratio=3.0, half_chord_sweep_deg=22.8,
              source='NASA TP-1538 Table I (300 ft2, 30 ft, 11.32 ft); half-chord sweep from the 40 deg leading edge and taper 0.23'),
    n_limit=9.0,
    limiter=dict(table_alpha_deg=[0.0, 15.0, 20.4, 25.0], table_n=[9.0, 9.0, 9.0 - 0.322 * 5.4, 9.0 - 0.322 * 5.4 - 1.322 * 4.6],
                 source='NASA TP-1538 Appendix A and figure 63: commanded load factor 8 g incremental up to 15 deg angle of attack, falling by '
                        '0.322 g/deg to 20.4 deg and by 1.322 g/deg above, about 25 deg at 1 g. This is the limiter of the simulated F-16A control system; the Block 50 limiter '
                        'is of the same form (9 g, about 25 deg).'),
    aero=dict(
        low_speed='trimmed lift and drag from the Stevens and Lewis tables (CX, CZ, Cm against angle of attack and stabilator), trim by Cm = 0 about 0.35 MAC, converted to wind axes. '
                  'The tables are low-speed wind-tunnel data (Mach 0.1 to 0.2).',
        mach_effects='ESTIMATE: (1) the drag polar CD(CL) of the low-speed table is used unchanged below the drag rise; (2) the angle of attack for a given CL falls with Mach by the ratio '
                     'of the Helmbold-Diederich lift slopes (aspect ratio 3, half-chord sweep 22.8 deg); (3) a zero-lift drag rise is added; (4) the usable lift coefficient is capped '
                     'against Mach number.',
        drag_rise=dict(mach=[0.0, 0.80, 0.85, 0.90, 0.95, 1.0], delta_cd=[0.0, 0.0, 0.0008, 0.0030, 0.0100, 0.0220],
                       source='ASSUMPTION: typical transonic drag rise of a 4 % thick fighter wing with a drag-divergence Mach number near 0.9; not F-16 data'),
        cl_cap=dict(mach=[0.0, 0.5, 0.7, 0.8, 0.9, 0.95], cl=[1.70, 1.70, 1.50, 1.35, 1.20, 1.10],
                    source='ASSUMPTION: usable (buffet and limiter) lift coefficient against Mach number; about 1.6 to 1.7 at low speed follows from the table at the 25 deg limit, the fall '
                           'with Mach number is a general trend for this class, not F-16 data. Plus or minus 10 %.'),
        leading_edge_flap='the reduced tables have no leading-edge flap input; the real aircraft schedules its flap with angle of attack and Mach number, which lowers drag at high lift. '
                          'The model may therefore have too much drag in a hard turn (too little sustained turn).',
        tip_missiles='no drag increment is added for the two tip missiles: the wind-tunnel model behind the tables is taken to carry them (not verified).',
        thrust_line='along the body axis: the lift gets T sin(alpha), the drag balance T cos(alpha)'),
    engine=dict(name=engines.F110['name'], source=engines.F110['source'], table_source=engines.F110['table_source'], scaling=engines.F110['scaling'],
                thrust_ab_sl_static_lbf=29500, thrust_mil_sl_static_lbf=17155),
    validity='Mach 0.2 to 0.95, sea level to 30,000 ft. Above Mach 0.9 the drag rise and lift cap are assumptions; the comparison uses the low-speed end.',
)


def _bil(tab, alpha_deg, de_deg):
    a = float(np.clip(alpha_deg, ALPHA[0], ALPHA[-1]))
    e = float(np.clip(de_deg, ELEV[0], ELEV[-1]))
    col = [float(np.interp(a, ALPHA, row)) for row in tab]
    return float(np.interp(e, ELEV, col))


def _trim_table():
    """Trimmed CL, CD and stabilator angle against angle of attack (low speed)."""
    al = np.arange(-2.0, 35.01, 0.25)
    cl, cd, de = [], [], []
    for a in al:
        es = np.linspace(-24, 24, 193)
        cm = np.array([_bil(CM, a, e) for e in es])
        i = int(np.argmin(np.abs(cm)))                      # Cm falls with stabilator angle
        if 0 < i < len(es) - 1:
            j = i if (cm[i] > 0) else i - 1
            e0 = es[j] + (es[j + 1] - es[j]) * cm[j] / (cm[j] - cm[j + 1])
        else:
            e0 = es[i]
        cx = _bil(CX, a, e0)
        cz = float(np.interp(a, ALPHA, CZ_ALPHA)) - 0.19 * e0 / 25.0
        ar = math.radians(a)
        cl.append(-cz * math.cos(ar) + cx * math.sin(ar))
        cd.append(-cx * math.cos(ar) - cz * math.sin(ar))
        de.append(e0)
    return al, np.array(cl), np.array(cd), np.array(de)


_AL, _CL, _CD, _DE = _trim_table()
_IMAX = int(np.argmax(_CL))


def _cla(mach, ar=3.0, sweep_half_deg=22.8):
    b2 = 1 - min(mach, 0.95) ** 2
    return 2 * math.pi * ar / (2 + math.sqrt(4 + ar * ar * (b2 + math.tan(math.radians(sweep_half_deg)) ** 2)))


class F16:
    """Aircraft object for perf.py."""
    name = 'F-16C Block 50 (estimate from public data)'

    def __init__(self, power='ab', weight_lb=None, thrust_factor=1.0, drag_factor=1.0, cl_cap_factor=1.0):
        self.power = power
        self.weight_lb = MODEL['weights']['weight_lb'] if weight_lb is None else weight_lb
        self.weight_N = self.weight_lb * LB * G0
        self.s_ref_m2 = 300.0 * FT2
        self.n_limit = MODEL['n_limit']
        self.thrust_factor, self.drag_factor, self.cl_cap_factor = thrust_factor, drag_factor, cl_cap_factor
        self.cl_scan_max = 1.75 * cl_cap_factor

    def thrust(self, mach, alt_m):
        return engines.thrust_f16(mach, alt_m, self.power, self.thrust_factor)

    def cl_cap(self, mach):
        c = MODEL['aero']['cl_cap']
        return float(np.interp(mach, c['mach'], c['cl'])) * self.cl_cap_factor

    def state(self, cl, mach, alt_m):
        if cl > min(self.cl_cap(mach), float(_CL[_IMAX]) * _cla(mach) / _cla(0.15)):
            return dict(ok=False, why='lift (usable CL cap)')
        k = _cla(mach) / _cla(0.15)
        alpha = float(np.interp(cl / k, _CL[:_IMAX + 1], _AL[:_IMAX + 1]))
        d = MODEL['aero']['drag_rise']
        cd = float(np.interp(cl, _CL[:_IMAX + 1], _CD[:_IMAX + 1])) * self.drag_factor + float(np.interp(mach, d['mach'], d['delta_cd']))
        lim = MODEL['limiter']
        n_cap = float(np.interp(alpha, lim['table_alpha_deg'], lim['table_n']))
        if alpha > lim['table_alpha_deg'][-1]:
            return dict(ok=False, why='angle-of-attack limiter')
        return dict(ok=True, cd=cd, alpha_rad=math.radians(alpha), n_cap=n_cap, cap_name='angle-of-attack limiter')


PUBLISHED = [
    dict(id='sea level, Mach 0.7, 22,000 lb', alt_ft=0, mach=0.7, weight_lb=22000, rate_deg_s=21.7, n=9.0,
         source='a DCS World forum post citing the Hellenic Air Force F-16 Block 50 flight manual: "sea level, 0.7 Mach, 21.7deg/sec, 9G"; a second post gives the best sustained rate '
                'near 460 kt at about 21.7 deg/s for 22,000 lb. Secondary source, read through a web search summary on 2026-11-13; the manual itself was not seen.'),
    dict(id='sea level, best sustained rate, 22,000 lb (lower figure)', alt_ft=0, mach=None, weight_lb=22000, rate_deg_s=19.5, n=None,
         source='another forum post: a clean Block 50 at 22,000 lb sustains 19.5 deg/s at sea level. It conflicts with the 21.7 deg/s figure; same search, secondary source.'),
    dict(id='5,000 ft, best sustained rate, 22,000 lb', alt_ft=5000, mach=None, weight_lb=22000, rate_deg_s=16.5, n=None,
         source='the same post as the 19.5 deg/s figure: 16.5 deg/s at 5,000 ft. Secondary source.'),
    dict(id='15,000 ft, Mach 0.8', alt_ft=15000, mach=0.8, weight_lb=22000, rate_deg_s=14.0, n=7.0,
         source='a general aviation blog: sustained 14 deg/s at Mach 0.8 and 15,000 ft, "7 g" (7 g at that speed is 15.1 deg/s, so the two numbers do not agree with each other). '
                'No manual citation and no weight; the weakest of the figures. 22,000 lb assumed here.'),
]


def check_published():
    out = []
    for p in PUBLISHED:
        ac = F16('ab', weight_lb=p['weight_lb'])
        alt = p['alt_ft'] * FT
        if p['mach'] is not None:
            r = perf.turn_table(ac, alt, [p['mach']])[0]
            what = 'at the published Mach number'
        else:
            rows = perf.turn_table(ac, alt, np.arange(0.3, 0.951, 0.01))
            ok = [x for x in rows if x['rate_sust_deg_s'] == x['rate_sust_deg_s']]
            r = max(ok, key=lambda x: x['rate_sust_deg_s'])
            what = 'best sustained rate of the model over Mach 0.3 to 0.95'
        out.append(dict(point=p['id'], published_rate_deg_s=p['rate_deg_s'], published_n=p['n'], source=p['source'],
                        model=dict(what=what, mach=round(r['mach'], 3), speed_kt=round(r['speed_m_s'] / KT), n_sustained=round(r['n_sust'], 2),
                                   rate_deg_s=round(r['rate_sust_deg_s'], 2), limited_by=r['cause_sust']),
                        mismatch_rate_pct=round(100 * (r['rate_sust_deg_s'] / p['rate_deg_s'] - 1), 1)))
    return out


def main():
    chk = check_published()
    ac = F16('ab')
    pol = [dict(alpha_deg=float(a), cl=round(float(c), 4), cd=round(float(d), 5), stabilator_deg=round(float(e), 2), lift_to_drag=round(float(c / d), 2))
           for a, c, d, e in zip(_AL, _CL, _CD, _DE) if abs(a - round(a)) < 1e-9 and a <= 30]
    pts = {}
    for alt_ft in (0, 15000, 30000):
        for pw in ('ab', 'mil'):
            a = F16(pw)
            pts['%d_ft_%s' % (alt_ft, pw)] = {('mach_%.1f' % m): round(a.thrust(m, alt_ft * FT) / LBF) for m in (0.2, 0.4, 0.6, 0.8, 0.9)}
    errs = [c['mismatch_rate_pct'] for c in chk]
    out = dict(
        what='F-16C Block 50 reference model', statement=MODEL['statement'], generated=time.strftime('%Y-%m-%d %H:%M'), generator='flight/ref/f16_model.py',
        model=MODEL,
        flight_condition=dict(weight_lb=ac.weight_lb, weight_kg=round(ac.weight_lb * LB, 1), wing_loading_lb_ft2=round(ac.weight_lb / 300.0, 1),
                              thrust_to_weight_ab_sl_static=round(29500 / ac.weight_lb, 3), thrust_to_weight_mil_sl_static=round(17155 / ac.weight_lb, 3)),
        trimmed_low_speed_polar=pol,
        lift_slope_ratio_to_low_speed={('mach_%.2f' % m): round(_cla(m) / _cla(0.15), 3) for m in (0.3, 0.5, 0.7, 0.85, 0.9)},
        installed_thrust_lbf=pts,
        tables=dict(alpha_deg=ALPHA, stabilator_deg=ELEV, cx=CX, cz_of_alpha=CZ_ALPHA, cz_rule='cz = cz_of_alpha - 0.19 * stabilator_deg / 25', cm=CM,
                    source='Stevens and Lewis reduced F-16 model as ported in AeroBenchVVPython (88ABW-2020-2188), from NASA TP-1538'),
        check_against_published=chk,
        mismatch=dict(rates_pct=errs,
                      reading='The published figures are secondary (forum posts and a blog quoting or paraphrasing a flight manual) and disagree with each other by about 10 %%. '
                              'The model lies %+.0f %% to %+.0f %% from them in sustained turn rate. Its low-speed, high-lift end, where the smallest turn radius occurs, has no published '
                              'figure to check against in this study: there it rests on the low-speed wind-tunnel tables without the leading-edge flap and on the scaled thrust table.' % (min(errs), max(errs))),
        uncertainty=dict(thrust='plus or minus 10 % (thrust table of another engine scaled by the rating ratio)',
                         drag_at_high_lift='the tables have no leading-edge flap: drag in a hard turn may be 10 to 20 % too high; rerun with drag x 0.85',
                         usable_lift='plus or minus 10 %', weight='plus or minus 800 lb',
                         effect='turn_performance.json reruns the F-16 smallest sustained radius at 15,000 ft with each of these'),
    )
    with open(os.path.join(HERE, 'f16_reference.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    for c in chk:
        print('%-55s published %.1f deg/s  model %.2f deg/s at Mach %.2f, n %.2f (%s)  %+.1f %%' % (c['point'], c['published_rate_deg_s'], c['model']['rate_deg_s'], c['model']['mach'],
                                                                                                 c['model']['n_sustained'], c['model']['limited_by'], c['mismatch_rate_pct']))
    for p in pol:
        if p['alpha_deg'] in (0, 5, 10, 15, 20, 25):
            print(p)
    print('wrote f16_reference.json')


if __name__ == '__main__':
    main()
