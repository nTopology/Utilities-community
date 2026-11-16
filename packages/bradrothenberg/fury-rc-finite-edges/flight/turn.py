"""Turn performance of the Fury model against an F-16C Block 50 reference: how tight at 9 g, 7 g, 5 g, 3 g, what it costs,
and what is left on roll-out.

    python flight/turn.py        ->  flight/out/turn.json, flight/out/turn.md  (charts: flight/charts.py)

Point performance in a level turn (ref/perf.py conventions): lift q S CL + T sin(alpha) = n W, specific excess power
Ps = V (T cos(alpha) - D) / W, radius V^2 / (g sqrt(n^2 - 1)). Both aircraft at 50 % internal fuel with two missiles,
maximum thrust (the F-16 with afterburner and at military power).

ESTIMATES. The Fury side rests on flight/aircraft.py (weights, thrust, lift limit and drag are estimates from the model
and public figures). The F-16 side is the public-data reference of ref/f16_model.py (low-speed wind-tunnel tables without
the leading-edge flap, a scaled thrust table), checked there against secondary published sustained-turn figures.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'ref'))
import aircraft as fa          # noqa: E402
import f16_model               # noqa: E402
from common import FT, KT, LB, LBF, G0, isa   # noqa: E402

OUT = HERE / 'out'
G_LEVELS = (9.0, 7.0, 5.0, 3.0)
ALTS_FT = (0.0, 15000.0)
MACH_SCAN = np.arange(0.16, 0.9501, 0.005)
MACH_TOP = 0.95
ORDER = ('fury', 'fury_light', 'f16_ab', 'f16_mil')
LABEL = dict(fury='Fury model, 6,730 lb', fury_light='Fury model, 5,000 lb', f16_ab='F-16C, afterburner', f16_mil='F-16C, military power')


def point(ac, n, mach, alt_m):
    """State in a level turn at load factor n, or None when the aircraft cannot fly it (lift limit, limiter, structure)."""
    if n > ac.n_limit + 1e-9:
        return None
    at = isa(alt_m)
    v = mach * at['a']
    q = 0.5 * at['rho'] * v * v
    t = ac.thrust(mach, alt_m)
    w, s = ac.weight_N, ac.s_ref_m2
    cl = n * w / (q * s)
    st = None
    for _ in range(6):
        if cl > ac.cl_scan_max:
            return None
        st = ac.state(cl, mach, alt_m)
        if not st['ok']:
            return None
        cl_new = (n * w - t * math.sin(st['alpha_rad'])) / (q * s)
        if abs(cl_new - cl) < 1e-6:
            break
        cl = cl_new
    if n > st.get('n_cap', 1e9) + 1e-9:
        return None
    d = q * s * st['cd']
    ps = v * (t * math.cos(st['alpha_rad']) - d) / w
    return dict(mach=mach, v=v, n=n, cl=cl, cd=st['cd'], alpha_deg=math.degrees(st['alpha_rad']), thrust_N=t, drag_N=d, ps=ps, q=q)


def n_max(ac, mach, alt_m):
    """Largest load factor available at a Mach number (lift, limiter or structure)."""
    lo, hi = 0.2, ac.n_limit
    if point(ac, hi, mach, alt_m):
        return hi
    if not point(ac, lo, mach, alt_m):
        return 0.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if point(ac, mid, mach, alt_m):
            lo = mid
        else:
            hi = mid
    return lo


def radius_rate(n, v):
    t = math.sqrt(max(n * n - 1.0, 1e-12))
    return v * v / (G0 * t), math.degrees(G0 * t / v)


def at_g(ac, n, alt_m):
    """Tightest turn at a load factor: the lowest speed at which it is available. And the tightest that thrust sustains."""
    ok = [float(m) for m in MACH_SCAN if point(ac, n, float(m), alt_m)]
    if not ok:
        return dict(n=n, available=False)
    lo, hi = max(ok[0] - 0.005, 0.05), ok[0]
    for _ in range(20):
        mid = 0.5 * (lo + hi)
        if point(ac, n, mid, alt_m):
            hi = mid
        else:
            lo = mid
    p = point(ac, n, hi, alt_m)
    r, w = radius_rate(n, p['v'])
    p1 = point(ac, 1.0, hi, alt_m)
    out = dict(n=n, available=True, mach=hi, speed_kt=p['v'] / KT, radius_ft=r / FT, rate_deg_s=w, ps_in_turn_ft_s=p['ps'] / FT, alpha_deg=p['alpha_deg'], cl=p['cl'],
               ps_1g_ft_s=(p1['ps'] / FT) if p1 else None, accel_1g_kt_s=(p1['ps'] * G0 / p['v'] / KT) if p1 else None,
               decel_in_turn_kt_s=p['ps'] * G0 / p['v'] / KT)
    sus = [m for m in ok if point(ac, n, m, alt_m)['ps'] >= 0.0]
    if sus:
        ps_ = point(ac, n, sus[0], alt_m)
        rs, ws = radius_rate(n, ps_['v'])
        out['sustained'] = dict(mach=sus[0], speed_kt=ps_['v'] / KT, radius_ft=rs / FT, rate_deg_s=ws, to_mach=sus[-1])
    else:
        out['sustained'] = None
    return out


def envelope(ac, alt_m):
    """Rate against speed: instantaneous limit and sustained (Ps = 0) line, excess power at 1 g and at the g levels."""
    rows = []
    at = isa(alt_m)
    for m in MACH_SCAN:
        m = float(m)
        ni = n_max(ac, m, alt_m)
        v = m * at['a']
        row = dict(mach=m, speed_kt=v / KT, n_inst=ni)
        p1 = point(ac, 1.0, m, alt_m)
        if ni > 1.001:
            pi = point(ac, ni, m, alt_m)
            row.update(rate_inst=radius_rate(ni, v)[1], radius_inst_ft=radius_rate(ni, v)[0] / FT, ps_inst_ft_s=pi['ps'] / FT)
            if pi['ps'] >= 0:
                ns = ni
            elif not p1 or p1['ps'] < 0:
                ns = float('nan')
            else:
                lo, hi = 1.0, ni
                for _ in range(30):
                    mid = 0.5 * (lo + hi)
                    if point(ac, mid, m, alt_m)['ps'] >= 0:
                        lo = mid
                    else:
                        hi = mid
                ns = lo
            row['n_sust'] = ns
            if ns == ns and ns > 1.001:
                row.update(rate_sust=radius_rate(ns, v)[1], radius_sust_ft=radius_rate(ns, v)[0] / FT)
        if p1:
            row['ps_1g_ft_s'] = p1['ps'] / FT
        for n in (3.0, 5.0, 7.0, 9.0):
            pn = point(ac, n, m, alt_m)
            if pn:
                row['ps_%dg_ft_s' % n] = pn['ps'] / FT
        rows.append(row)
    return rows


def regain(ac, v, v_target, alt_m, dt=0.05):
    """Time at 1 g and maximum thrust from v back to v_target (None: not within 5 minutes)."""
    at = isa(alt_m)
    if v >= v_target:
        return 0.0
    t = 0.0
    while v < v_target and t < 300.0:
        p = point(ac, 1.0, v / at['a'], alt_m)
        if not p or p['ps'] <= 0:
            return None
        v += G0 * p['ps'] / v * dt
        t += dt
    return t if v >= v_target else None


def half_turn(ac, n_cmd, mach0, alt_m, dt=0.02):
    """180 deg level turn at maximum thrust from an entry speed, holding the load factor asked for or, where that is not available, the
    most the aircraft has. Point mass, constant height. Returns time, exit speed, turn diameter and the excess power on roll-out."""
    at = isa(alt_m)
    v = mach0 * at['a']
    chi, y, t = 0.0, 0.0, 0.0
    n_low, n = 99.0, n_cmd
    while chi < math.pi and t < 120.0:
        m = v / at['a']
        n = min(n_cmd, n_max(ac, m, alt_m))
        if n <= 1.02:
            return dict(completed=False, why='the load factor falls to 1 g at %.0f kt' % (v / KT), time_s=t)
        p = point(ac, n, m, alt_m)
        y += v * math.sin(chi) * dt
        chi += G0 * math.sqrt(n * n - 1.0) / v * dt
        v = min(v + G0 * p['ps'] / v * dt, MACH_TOP * at['a'])        # the throttle is pulled back at the top Mach number of the models
        t += dt
        n_low = min(n_low, n)
    m = v / at['a']
    p1 = point(ac, 1.0, m, alt_m)
    v0 = mach0 * at['a']
    return dict(completed=True, n_asked=n_cmd, entry_kt=v0 / KT, entry_mach=mach0, time_s=t, exit_kt=v / KT, exit_mach=m, speed_change_kt=(v - v0) / KT,
                n_at_exit=n, n_lowest=n_low, diameter_ft=abs(y) / FT, mean_rate_deg_s=180.0 / t,
                ps_exit_1g_ft_s=(p1['ps'] / FT) if p1 else None, accel_exit_kt_s=(p1['ps'] * G0 / v / KT) if p1 else None,
                time_to_regain_entry_speed_s=regain(ac, v, v0, alt_m))


def aircraft_set():
    return [('fury', fa.Fury('combat')), ('fury_light', fa.Fury('light')), ('f16_ab', f16_model.F16('ab')), ('f16_mil', f16_model.F16('mil'))]


def sensitivity(alt_m=0.0):
    """How far the Fury answers move with the main assumptions: 9 g corner radius and 5 g sustained speed at sea level."""
    rows = []
    for label, kw in (('as stated', {}), ('usable CLmax + 0.15', dict(cl_max_delta=0.15)), ('usable CLmax - 0.15', dict(cl_max_delta=-0.15)),
                      ('thrust + 15 %', dict(thrust_factor=1.15)), ('thrust - 15 %', dict(thrust_factor=0.85)),
                      ('drag + 15 %', dict(drag_factor=1.15)), ('drag - 15 %', dict(drag_factor=0.85)),
                      ('drag as the flow solution gives it', dict(flow_polar=True))):
        ac = fa.Fury('combat', **kw)
        g9, g5 = at_g(ac, 9.0, alt_m), at_g(ac, 5.0, alt_m)
        env = envelope(ac, alt_m)
        ok = [r for r in env if 'rate_sust' in r]
        best = max(ok, key=lambda r: r['n_sust']) if ok else None
        rows.append(dict(case=label, radius_9g_ft=g9.get('radius_ft'), speed_9g_kt=g9.get('speed_kt'), ps_9g_ft_s=g9.get('ps_in_turn_ft_s'),
                         sustained_5g=bool(g5.get('sustained')), max_sustained_g=best['n_sust'] if best else None))
    return rows


def main():
    OUT.mkdir(exist_ok=True)
    st = fa.statement()
    acs = aircraft_set()
    res = dict(what='Level-turn point performance, Fury model against an F-16C Block 50 reference (estimates)', g_levels=G_LEVELS, altitudes_ft=ALTS_FT,
               aircraft={k: dict(label=LABEL[k], weight_lb=round(ac.weight_N / G0 / LB), wing_area_ft2=round(ac.s_ref_m2 / FT ** 2, 1),
                                 wing_loading_lb_ft2=round(ac.weight_N / G0 / LB / (ac.s_ref_m2 / FT ** 2), 1),
                                 thrust_sl_mach_0p5_lbf=round(ac.thrust(0.5, 0.0) / LBF), thrust_to_weight_sl_mach_0p5=round(ac.thrust(0.5, 0.0) / ac.weight_N, 2)) for k, ac in acs},
               by_altitude={})
    for alt_ft in ALTS_FT:
        alt = alt_ft * FT
        blk = {}
        for k, ac in acs:
            env = envelope(ac, alt)
            ok_i = [r for r in env if 'rate_inst' in r]
            ok_s = [r for r in env if 'rate_sust' in r]
            best_i = max(ok_i, key=lambda r: r['rate_inst'])
            tight_i = min(ok_i, key=lambda r: r['radius_inst_ft'])
            best_s = max(ok_s, key=lambda r: r['rate_sust']) if ok_s else None
            tight_s = min(ok_s, key=lambda r: r['radius_sust_ft']) if ok_s else None
            max_g_s = max(ok_s, key=lambda r: r['n_sust']) if ok_s else None
            top = [r for r in env if r.get('ps_1g_ft_s', -1) >= 0]
            best_ps = max(env, key=lambda r: r.get('ps_1g_ft_s', -1e9))
            blk[k] = dict(g=[at_g(ac, n, alt) for n in G_LEVELS], envelope=env,
                          corner=dict(mach=best_i['mach'], speed_kt=best_i['speed_kt'], n=best_i['n_inst'], rate_deg_s=best_i['rate_inst'], radius_ft=best_i['radius_inst_ft'], ps_ft_s=best_i['ps_inst_ft_s']),
                          tightest_instantaneous=dict(mach=tight_i['mach'], speed_kt=tight_i['speed_kt'], n=tight_i['n_inst'], radius_ft=tight_i['radius_inst_ft'], rate_deg_s=tight_i['rate_inst']),
                          best_sustained_rate=None if not best_s else dict(mach=best_s['mach'], speed_kt=best_s['speed_kt'], n=best_s['n_sust'], rate_deg_s=best_s['rate_sust'], radius_ft=best_s['radius_sust_ft']),
                          tightest_sustained=None if not tight_s else dict(mach=tight_s['mach'], speed_kt=tight_s['speed_kt'], n=tight_s['n_sust'], radius_ft=tight_s['radius_sust_ft'], rate_deg_s=tight_s['rate_sust']),
                          max_sustained_g=None if not max_g_s else dict(mach=max_g_s['mach'], speed_kt=max_g_s['speed_kt'], n=max_g_s['n_sust']),
                          max_level_mach=max(r['mach'] for r in top) if top else None,
                          best_ps_1g=dict(mach=best_ps['mach'], ps_ft_s=best_ps.get('ps_1g_ft_s')))
            print('%6.0f ft %-11s corner %.0f kt %.1f g %.1f deg/s %.0f ft | best sustained %s | max level Mach %s' % (
                alt_ft, k, best_i['speed_kt'], best_i['n_inst'], best_i['rate_inst'], best_i['radius_inst_ft'],
                ('%.1f g %.1f deg/s at %.0f kt' % (best_s['n_sust'], best_s['rate_sust'], best_s['speed_kt'])) if best_s else 'none', blk[k]['max_level_mach']), flush=True)
        entry = 0.70 if alt_ft == 0 else 0.80
        blk['half_turns'] = dict(entry_mach=entry, rows={k: [half_turn(ac, n, entry, alt) for n in G_LEVELS] for k, ac in acs})
        res['by_altitude']['%.0f' % alt_ft] = blk
    res['sensitivity_sea_level'] = sensitivity()
    (OUT / 'turn.json').write_text(json.dumps(res, indent=1, default=float))
    write_md(res)


def write_md(res):
    f = lambda v, fmt='%.0f': '–' if v is None or v != v else fmt % v
    c0 = lambda v: format(round(v, -1), ',.0f')
    md = ['# Turn performance: Fury model against an F-16C (estimates)', '',
          'Level turns at maximum thrust. Both aircraft with half their internal fuel and two missiles. The Fury numbers come from the weight, thrust, lift and drag '
          'estimates in aircraft.md; the F-16 numbers from a public-data reference model. Read differences of 10 to 15 % as within the uncertainty.', '',
          '| Aircraft | Weight [lb] | Wing loading [lb/ft2] | Thrust at sea level, Mach 0.5 [lbf] | Thrust / weight there |', '|---|---:|---:|---:|---:|']
    for k, a in res['aircraft'].items():
        md.append('| %s | %s | %.1f | %s | %.2f |' % (a['label'], format(a['weight_lb'], ','), a['wing_loading_lb_ft2'], format(a['thrust_sl_mach_0p5_lbf'], ','), a['thrust_to_weight_sl_mach_0p5']))
    for alt, blk in res['by_altitude'].items():
        name = 'Sea level' if alt == '0' else '%s ft' % format(int(alt), ',')
        md += ['', '## %s' % name, '', '### Tightest turn at each load factor (the lowest speed at which it is available)', '',
               '| Load factor | Aircraft | Speed [kt true] | Mach | Radius [ft] | Rate [deg/s] | Excess power in the turn [ft/s] | Speed change [kt/s] | Excess power at 1 g on roll-out [ft/s] | Sustained at this g? |',
               '|---:|---|---:|---:|---:|---:|---:|---:|---:|---|']
        for i, n in enumerate(res['g_levels']):
            for k in ORDER:
                r = blk[k]['g'][i]
                if not r['available']:
                    md.append('| %.0f g | %s | not available below Mach 0.95 | | | | | | | |' % (n, LABEL[k]))
                    continue
                s = r['sustained']
                sus = 'no' if not s else 'from %.0f kt (radius %s ft)' % (s['speed_kt'], c0(s['radius_ft']))
                md.append('| %.0f g | %s | %.0f | %.2f | %s | %.1f | %+.0f | %+.1f | %s | %s |' % (
                    n, LABEL[k], r['speed_kt'], r['mach'], c0(r['radius_ft']), r['rate_deg_s'], r['ps_in_turn_ft_s'], r['decel_in_turn_kt_s'], f(r['ps_1g_ft_s'], '%+.0f'), sus))
        md += ['', '### Limits of the envelope', '',
               '| Aircraft | Best instantaneous rate | Tightest instantaneous radius | Best sustained rate | Tightest sustained radius | Most g sustained | Top level speed [Mach] | Best 1 g excess power [ft/s] |',
               '|---|---|---|---|---|---|---:|---:|']
        for k in ORDER:
            b = blk[k]
            c, ti, bs, ts, mg = b['corner'], b['tightest_instantaneous'], b['best_sustained_rate'], b['tightest_sustained'], b['max_sustained_g']
            md.append('| %s | %.1f deg/s at %.0f kt, %.1f g | %s ft at %.0f kt, %.1f g | %s | %s | %s | %s | %.0f |' % (
                LABEL[k], c['rate_deg_s'], c['speed_kt'], c['n'], c0(ti['radius_ft']), ti['speed_kt'], ti['n'],
                '–' if not bs else '%.1f deg/s at %.0f kt, %.1f g' % (bs['rate_deg_s'], bs['speed_kt'], bs['n']),
                '–' if not ts else '%s ft at %.0f kt, %.1f g' % (c0(ts['radius_ft']), ts['speed_kt'], ts['n']),
                '–' if not mg else '%.1f g at %.0f kt' % (mg['n'], mg['speed_kt']), f(b['max_level_mach'], '%.2f'), b['best_ps_1g']['ps_ft_s']))
        h = blk['half_turns']
        md += ['', '### A 180 deg turn from Mach %.2f at maximum thrust (point mass, constant height)' % h['entry_mach'], '',
               'The load factor asked for is held while the aircraft has it; when the speed falls below what the lift limit needs, the turn goes on at the most it has.', '',
               '| Load factor asked | Aircraft | Time [s] | Turn diameter [ft] | Entry [kt] | Exit [kt] | g at the exit | Excess power at 1 g on roll-out [ft/s] | Time to regain the entry speed [s] |',
               '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
        for i, n in enumerate(res['g_levels']):
            for k in ORDER:
                r = h['rows'][k][i]
                if not r['completed']:
                    md.append('| %.0f g | %s | not completed: %s | | | | | | |' % (n, LABEL[k], r['why']))
                    continue
                md.append('| %.0f g | %s | %.1f | %s | %.0f | %.0f | %.1f | %s | %s |' % (n, LABEL[k], r['time_s'], c0(r['diameter_ft']), r['entry_kt'], r['exit_kt'], r['n_at_exit'],
                                                                                  f(r['ps_exit_1g_ft_s'], '%+.0f'), f(r['time_to_regain_entry_speed_s'], '%.0f')))
    md += ['', '## How far the Fury answers move with the assumptions (sea level, 6,730 lb)', '',
           '| Case | 9 g: lowest speed [kt] | 9 g: radius [ft] | 9 g: excess power [ft/s] | Most g sustained | 5 g sustained? |', '|---|---:|---:|---:|---:|---|']
    for r in res['sensitivity_sea_level']:
        md.append('| %s | %s | %s | %s | %s | %s |' % (r['case'], f(r['speed_9g_kt']), '–' if r['radius_9g_ft'] is None else c0(r['radius_9g_ft']), f(r['ps_9g_ft_s'], '%+.0f'),
                                                   f(r['max_sustained_g'], '%.1f'), 'yes' if r['sustained_5g'] else 'no'))
    (OUT / 'turn.md').write_text('\n'.join(md), encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
