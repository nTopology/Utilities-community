"""Point performance in a level turn, the same function for the UAS variants and the F-16 reference. Numpy only.

An aircraft object gives: weight_N, s_ref_m2, n_limit, thrust(mach, alt_m) in N, cl_scan_max, and
state(cl, mach, alt_m) -> dict(cd, alpha_rad, ok, why, n_cap) where cl is the total (trimmed) lift coefficient,
ok is False beyond the lift limit of the aircraft (why names it) and n_cap is an optional load-factor limit that
depends on the state (the angle-of-attack limiter of the F-16).

Level turn at constant speed and altitude: lift L = q S CL + T sin(alpha) = n W; sustained when T cos(alpha) >= q S CD.
Radius R = V^2 / (g sqrt(n^2 - 1)); rate = g sqrt(n^2 - 1) / V. The thrust line is taken along the body axis.
"""
from __future__ import annotations
import math
import numpy as np
from common import G0, isa


def turn_point(ac, mach, alt_m, ncl=260):
    """Largest instantaneous and sustained load factor at one Mach number and altitude, with the cause of each limit."""
    at = isa(alt_m)
    v = mach * at['a']
    q = 0.5 * at['rho'] * v * v
    thrust = ac.thrust(mach, alt_m)
    w, s = ac.weight_N, ac.s_ref_m2
    rows = []                                   # (n, excess thrust N, cl, alpha, state)
    end = 'lift'

    def point(cl):
        st = ac.state(float(cl), mach, alt_m)
        if not st['ok']:
            return None, st
        n = (q * s * cl + thrust * math.sin(st['alpha_rad'])) / w
        cap = min(ac.n_limit, st.get('n_cap', 1e9))
        ex = thrust * math.cos(st['alpha_rad']) - q * s * st['cd']
        return (n, ex, float(cl), st['alpha_rad'], st, cap), st

    cl_prev = None
    for cl in np.linspace(0.004, ac.cl_scan_max, ncl):
        p, st = point(cl)
        if p is None or p[0] > p[5]:
            # the limit lies between cl_prev and cl: bisect to it (lift limit, elevon travel, limiter or structural limit)
            lo, hi, last_bad = (cl_prev if cl_prev is not None else 0.0), float(cl), (p, st)
            for _ in range(14):
                mid = 0.5 * (lo + hi)
                pm_, sm_ = point(mid)
                if pm_ is None or pm_[0] > pm_[5]:
                    hi, last_bad = mid, (pm_, sm_)
                else:
                    lo = mid
                    rows.append(pm_[:5])
            pb, sb = last_bad
            if pb is None:
                end = sb.get('why', 'lift')
            else:
                end = 'structural' if pb[5] >= ac.n_limit - 1e-9 else sb.get('cap_name', 'limiter')
            break
        rows.append(p[:5])
        cl_prev = float(cl)
    rows.sort(key=lambda r_: r_[2])
    out = dict(mach=mach, speed_m_s=v, q_Pa=q, thrust_N=thrust)
    if not rows:
        return dict(out, n_inst=float('nan'), n_sust=float('nan'), cause_inst=end, cause_sust='no level flight')
    n_inst, ex_i, cl_i, a_i, st_i = rows[-1]
    out.update(n_inst=n_inst, cause_inst=end, cl_inst=cl_i, alpha_inst_deg=math.degrees(a_i))
    pos = [i for i, r in enumerate(rows) if r[1] >= 0]
    if not pos:
        return dict(out, n_sust=float('nan'), cause_sust='thrust below drag at every lift')
    i = pos[-1]
    if i == len(rows) - 1:
        n_s, cl_s, a_s, st_s, cause = n_inst, cl_i, a_i, st_i, end
        ex_s = ex_i
    else:
        n0, ex0, cl0, a0, s0 = rows[i]
        n1, ex1, cl1, a1, s1 = rows[i + 1]
        f = ex0 / max(ex0 - ex1, 1e-9)
        n_s, cl_s, a_s, st_s, cause, ex_s = n0 + f * (n1 - n0), cl0 + f * (cl1 - cl0), a0 + f * (a1 - a0), s0, 'thrust', 0.0
    out.update(n_sust=n_s, cause_sust=cause, cl_sust=cl_s, alpha_sust_deg=math.degrees(a_s), excess_thrust_N=ex_s,
               extra={k: v_ for k, v_ in st_s.items() if k in ('delta_deg', 'cl_wing', 'cd', 'command_deg', 'reserve_left_deg', 'cm_thrust', 'qhat', 'static_margin', 'cm0')})
    return out


def radius_rate(n, v):
    if not (n == n) or n <= 1.0005:
        return float('nan'), float('nan')
    t = math.sqrt(n * n - 1.0)
    return v * v / (G0 * t), math.degrees(G0 * t / v)


def turn_table(ac, alt_m, machs, ncl=260):
    rows = []
    for m in machs:
        p = turn_point(ac, float(m), alt_m, ncl)
        r_s, w_s = radius_rate(p['n_sust'], p['speed_m_s'])
        r_i, w_i = radius_rate(p['n_inst'], p['speed_m_s'])
        p.update(radius_sust_m=r_s, rate_sust_deg_s=w_s, radius_inst_m=r_i, rate_inst_deg_s=w_i)
        rows.append(p)
    return rows


def smallest(rows, key='radius_sust_m'):
    ok = [r for r in rows if r[key] == r[key]]
    return min(ok, key=lambda r: r[key]) if ok else None


def smallest_refined(ac, alt_m, rows, key='radius_sust_m', step=0.0025, ncl=260):
    """Smallest radius on the table, then a finer Mach step around it."""
    b = smallest(rows, key)
    if b is None:
        return None
    dm = rows[1]['mach'] - rows[0]['mach']
    fine = turn_table(ac, alt_m, np.arange(max(b['mach'] - dm, 0.05), b['mach'] + dm + 1e-9, step), ncl)
    return smallest(fine + [b], key)


def level_flight(ac, mach, alt_m):
    """1 g level flight: dict(ok, cl, cd, lift_to_drag, drag_N, thrust_N, alpha_deg). Thrust inclination is neglected here."""
    at = isa(alt_m)
    v = mach * at['a']
    q = 0.5 * at['rho'] * v * v
    cl = ac.weight_N / (q * ac.s_ref_m2)
    if cl > ac.cl_scan_max:
        return dict(ok=False)
    st = ac.state(cl, mach, alt_m)
    if not st['ok']:
        return dict(ok=False)
    d = q * ac.s_ref_m2 * st['cd']
    return dict(ok=True, cl=cl, cd=st['cd'], lift_to_drag=cl / st['cd'], drag_N=d, thrust_N=ac.thrust(mach, alt_m), alpha_deg=math.degrees(st['alpha_rad']),
                speed_m_s=v, extra={k: v_ for k, v_ in st.items() if k in ('delta_deg', 'command_deg')})


def max_level_mach(ac, alt_m, m_top=0.95, step=0.005):
    best = None
    for m in np.arange(0.15, m_top + 1e-9, step):
        lf = level_flight(ac, float(m), alt_m)
        if lf['ok'] and lf['thrust_N'] >= lf['drag_N']:
            best = float(m)
    return best
