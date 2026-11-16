"""The flights of the Fury 6-DOF model: the landing approach with gear and flap down, and the hard turns.

    python flight/sim/maneuvers.py [approach] [turns] [--verify]

Every flight runs in the native Unlinked engine (run.py); this script only writes the commands and reads the traces.
Results: flight/sim/runs/<name>/ (trace.json, raw.npz, params.json, init.m, summary.json) and flight/out/flights.json
with the numbers measured from the traces in US customary units.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

SIM = Path(__file__).resolve().parent
FLIGHT = SIM.parent
sys.path.insert(0, str(SIM))
import fly  # noqa: E402
import schedule as S  # noqa: E402

DEG = math.pi / 180.0
FT, KT, LBF, G0, NM = 0.3048, 0.514444444, 4.4482216153, 9.80665, 1852.0
IN = 0.0254
RUNS = SIM / 'runs'
OUT = FLIGHT / 'out'

TURNS = [
    # name, entry Mach, height ft, load factor asked, track change deg, hold speed, Mach of the coefficient tables, seconds
    dict(name='turn_5g_sl', mach=0.60, alt_ft=1000, g=5.0, change=360, hold=1, table_mach=0.6, stop=45,
         what='5 g turn through 360 deg at Mach 0.60, 1,000 ft, speed held with thrust'),
    dict(name='turn_7g_sl', mach=0.70, alt_ft=1000, g=7.0, change=180, hold=0, table_mach=0.6, stop=45,
         what='7 g turn through 180 deg from Mach 0.70, 1,000 ft, speed let go, then roll out and accelerate back'),
    dict(name='turn_9g_sl', mach=0.70, alt_ft=1000, g=9.0, change=180, hold=0, table_mach=0.6, stop=45,
         what='9 g turn through 180 deg from Mach 0.70, 1,000 ft, speed let go, then roll out and accelerate back'),
    dict(name='turn_9g_360_sl', mach=0.70, alt_ft=1000, g=9.0, change=360, hold=0, table_mach=0.5, stop=60,
         what='9 g turn through 360 deg from Mach 0.70, 1,000 ft, speed let go: the turn ends on the lift limit'),
    dict(name='turn_9g_15k', mach=0.80, alt_ft=15000, g=9.0, change=180, hold=0, table_mach=0.7, stop=90,
         what='9 g turn through 180 deg from Mach 0.80, 15,000 ft, speed let go, then roll out and accelerate back'),
    dict(name='turn_5g_15k', mach=0.80, alt_ft=15000, g=5.0, change=180, hold=0, table_mach=0.7, stop=90,
         what='5 g turn through 180 deg from Mach 0.80, 15,000 ft, speed let go, then roll out and accelerate back'),
]
T_CMD = 3.0


def specific_excess_power(t, d):
    """Ps = dh/dt + (V / g) dV/dt, m/s, from the trace."""
    return d['climb_rate'] + d['tas'] * np.gradient(d['tas'], t) / G0


def turn_numbers(t, d, case):
    """What the turn did, measured from the trace."""
    chi = d['track_unwrapped']
    target = case['change'] * DEG
    vh = np.hypot(d['vn'], d['ve'])
    rate = np.gradient(chi, t)
    ps = specific_excess_power(t, d)
    k0 = int(np.searchsorted(t, T_CMD))
    k_end = int(np.argmax(chi >= target - 5.0 * DEG)) if np.any(chi >= target - 5.0 * DEG) else len(t) - 1      # within 5 deg of the new track
    hard = (np.arange(len(t)) > k0) & (np.arange(len(t)) < k_end) & (d['nz'] >= 0.9 * d['nz'][k0:k_end + 1].max())
    # wings level after the turn: bank within 5 deg and staying there
    lvl = np.abs(d['phi']) < 5.0 * DEG
    k_out = next((k for k in range(k_end, len(t) - 240) if lvl[k:k + 240].all()), len(t) - 1)
    # power coming out: the first 3 s after the turn with the wings within 10 deg of level, 0.85 to 1.15 g and full throttle
    ok = np.where((np.arange(len(t)) >= k_end) & (np.abs(d['phi']) < 10.0 * DEG) & (np.abs(d['nz'] - 1.0) < 0.15) & (d['throttle'] >= 0.999) & (d['spool'] >= 0.98))[0]
    two = ok[:720] if len(ok) else np.array([k_out])
    k_out = int(two[0])
    k_back = next((k for k in range(k_out, len(t)) if d['tas'][k] >= 0.995 * d['tas'][0]), None)
    radius = vh / np.maximum(np.abs(rate), 1e-9)
    kh = np.where(hard)[0]
    # ground track: distance of the path across the entry line
    across = d['pe'] - d['pe'][k0]
    along = d['pn'] - d['pn'][k0]
    out = dict(
        what=case['what'], entry=dict(speed_kt=d['tas'][0] / KT, mach=float(d['mach'][0]), altitude_ft=d['height'][0] / FT),
        load_factor_asked_g=case['g'], peak_load_factor_g=float(d['nz'][k0:k_end + 1].max()),
        mean_load_factor_in_hard_part_g=float(d['nz'][kh].mean()),
        time_to_turn_s=float(t[k_end] - T_CMD), track_change_deg=case['change'],
        mean_turn_rate_deg_s=float(case['change'] / (t[k_end] - T_CMD)), peak_turn_rate_deg_s=float(rate[k0:k_end + 1].max() / DEG),
        mean_turn_rate_in_hard_part_deg_s=float(rate[kh].mean() / DEG),
        tightest_radius_ft=float(radius[kh].min() / FT), mean_radius_in_hard_part_ft=float(radius[kh].mean() / FT),
        ground_track_width_ft=float(np.abs(across[k0:k_end + 1]).max() / FT), ground_track_length_ft=float((along[k0:k_end + 1].max() - along[k0:k_end + 1].min()) / FT),
        speed_at_end_of_turn_kt=float(d['tas'][k_end] / KT), lowest_speed_kt=float(d['tas'][k0:k_out + 1].min() / KT),
        speed_lost_kt=float((d['tas'][0] - d['tas'][k0:k_out + 1].min()) / KT),
        speed_change_in_hard_part_kt_per_s=float((d['tas'][kh[-1]] - d['tas'][kh[0]]) / KT / (t[kh[-1]] - t[kh[0]])),
        excess_power_in_hard_part_ft_s=float(ps[kh].mean() / FT), throttle_in_hard_part=float(d['throttle'][kh].mean()),
        hard_part_s=[float(t[kh[0]]), float(t[kh[-1]])], load_factor_above_limit_s=float(np.sum(d['nz'] > 9.0) * (t[1] - t[0])),
        peak_alpha_deg=float(d['alpha'][k0:k_end + 1].max() / DEG), alpha_limiter_deg=None,
        height_change_ft=[float((d['height'][k0:k_out + 1].min() - d['height'][0]) / FT), float((d['height'][k0:k_out + 1].max() - d['height'][0]) / FT)],
        wings_level_at_s=float(t[k_out]), speed_at_wings_level_kt=float(d['tas'][k_out] / KT), roll_out_window_s=[float(t[two[0]]), float(t[two[-1]])],
        excess_power_after_roll_out_ft_s=float(ps[two].mean() / FT), throttle_after_roll_out=float(d['throttle'][two].mean()),
        acceleration_after_roll_out_kt_per_s=float(np.gradient(d['tas'], t)[two].mean() / KT),
        time_to_regain_entry_speed_s=None if k_back is None else float(t[k_back] - t[k_out]),
        peak_roll_rate_deg_s=float(np.abs(d['p']).max() / DEG), peak_sideslip_deg=float(np.abs(d['beta']).max() / DEG),
        stabilator_range_deg=[float(d['stabilator'].min() / DEG), float(d['stabilator'].max() / DEG)])
    return out


def fly_turn(case, verify=False, log=print):
    par = fly.start('combat', case['mach'], case['alt_ft'], hold_speed=case['hold'], table_mach=case['table_mach'], maneuver=case['what'], log=log)
    rows = [dict(t=T_CMD, heading_change_deg=case['change'], turn_g=case['g'])]
    if not case['hold']:
        rows[0]['throttle'] = 1.0           # full thrust from the start of the turn
    sched = dict(description=case['what'], duration_s=case['stop'], commands=rows, condition=dict(case='combat', mach=case['mach'], altitude_ft=case['alt_ft']))
    fl = fly.Flight(par, RUNS / case['name'], log=log)
    fl.t_far_min = case['stop']
    fl.command(rows[0])
    # fly until the track is within 2 deg of the target; then full thrust, wings level, for at least 6 s and until the entry speed is back;
    # then hold the entry Mach number again
    target = case['change'] * DEG
    tt = T_CMD + 2.0
    while tt < case['stop'] - 8.0:
        fl.advance(tt)
        if fl.data['track_unwrapped'][-1] >= target - 2.0 * DEG:
            break
        tt += 0.5
    t_end = fl.t_done
    if case['hold']:
        fl.command(dict(t=t_end, throttle=1.0, ramp_s=0.5))
    while tt < case['stop'] - 2.0:
        tt += 0.5
        fl.advance(tt)
        if tt >= t_end + 6.0 and fl.data['tas'][-1] >= 0.998 * fl.data['tas'][0]:
            break
    fl.command(dict(t=fl.t_done, mach=case['mach'], ramp_s=0.5))
    fl.advance(case['stop'])
    summ = fl.finish(verify, dict(description=case['what'], condition=sched['condition']))
    res = turn_numbers(fl.t, fl.data, case)
    res['alpha_limiter_deg'] = par['workspace']['alpha_lim'] / DEG
    res['table_mach'] = case['table_mach']
    res['warnings'] = summ['warnings']
    res['checks'] = summ['checks']
    if verify:
        res['python_reference'] = {k: summ['reference'][k] for k in ('worst', 'passed', 'tolerance_relative_to_scale')}
    log(f"  {case['name']}: peak {res['peak_load_factor_g']:.2f} g, {res['time_to_turn_s']:.1f} s for {case['change']} deg, tightest radius {res['tightest_radius_ft']:,.0f} ft, "
        f"speed {res['entry']['speed_kt']:.0f} -> {res['lowest_speed_kt']:.0f} kt, Ps in the turn {res['excess_power_in_hard_part_ft_s']:+.0f} ft/s, "
        f"after roll-out {res['excess_power_after_roll_out_ft_s']:+.0f} ft/s")
    return res


# ---------------------------------------------------------------------------------------------------------------- landing approach
APPROACH = dict(case='landing', start_kt=160.0, start_ft=1200.0, approach_kt=110.0, path_deg=3.0, flap_deg=30.0, flare_wheel_ft=45.0, flare_sink_fpm=150.0,
                table_mach=0.2, bank_deg=30.0)


def wheel_geometry(par):
    """Main-wheel contact point from the centre of gravity, body axes (x forward, z down), m: from the design inputs of the model."""
    st = json.loads((OUT / 'aircraft.json').read_text())
    cg = par['physical']['cg_m']
    ground_line_m = 47.0 * IN            # design input 'ground_line': ground below the fuselage reference line, aircraft standing on its wheels
    return dict(x=-(st['balance']['main_gear_station_m'] - cg[0]), z=cg[2] + ground_line_m, x_nose=-(st['balance']['nose_gear_station_m'] - cg[0]))


def wheel_height(d, geo):
    """Height of the lower main wheel above the height datum, m (bank included)."""
    th, ph = d['theta'], d['phi']
    half_track = 67.5 * IN / 2
    down = lambda y: -geo['x'] * np.sin(th) + y * np.sin(ph) * np.cos(th) + geo['z'] * np.cos(ph) * np.cos(th)
    return d['height'] - np.maximum(down(half_track), down(-half_track))


def fly_approach(verify=False, log=print):
    A = APPROACH
    isa_a = 340.294 * math.sqrt((288.15 - 0.0065 * A['start_ft'] * FT) / 288.15)
    par = fly.start(A['case'], A['start_kt'] * KT / isa_a, A['start_ft'], table_mach=A['table_mach'],
                    maneuver='landing approach: base turn, gear and flap down, 3 deg final, flare to touchdown', log=log)
    geo = wheel_geometry(par)
    fl = fly.Flight(par, RUNS / 'approach', log=log)
    fl.t_far_min = 400.0
    sink = A['approach_kt'] * KT * math.sin(A['path_deg'] * DEG)                 # m/s on the final
    t_desc = 45.0
    t_ramp = (A['start_ft'] * FT) / sink                                         # the height command reaches the datum after this long
    for row in (dict(t=2.0, gear='down', note='gear down on the base leg'),
                dict(t=4.0, heading_change_deg=90.0, bank_limit_deg=A['bank_deg'], note='base turn to final'),
                dict(t=6.0, flap_deg=A['flap_deg'], ramp_s=8.0, note='flap down'),
                dict(t=6.0, speed_kt=A['approach_kt'], ramp_s=25.0, note='slow to the approach speed'),
                dict(t=t_desc, altitude_ft=0.0, ramp_s=t_ramp, climb_rate_fpm=1500.0, note=f'final: {A["path_deg"]:.0f} deg path')):
        fl.command(row)
    # fly down the path until the main wheels are at the flare height, then flare
    tt = t_desc + t_ramp * 0.8
    fl.advance(tt)
    while wheel_height(fl.data, geo)[-1] > A['flare_wheel_ft'] * FT and tt < 390.0:
        tt += 0.25
        fl.advance(tt)
    t_flare = fl.t_done
    fl.command(dict(t=t_flare, altitude_ft=-30.0, climb_rate_fpm=A['flare_sink_fpm'], throttle=0.0, ramp_s=0.5, note='flare: sink rate cut, throttle to idle'))
    while wheel_height(fl.data, geo)[-1] > 0.0 and tt < 395.0:
        tt += 0.25
        fl.advance(tt)
    summ = fl.finish(verify, dict(description=par['maneuver'], condition=dict(case=A['case'], altitude_ft=A['start_ft'], speed_kt=A['start_kt'])))
    t, d = fl.t, fl.data
    hw = wheel_height(d, geo)
    k_td = int(np.argmax(hw <= 0.0)) if np.any(hw <= 0.0) else len(t) - 1
    k_fl = int(np.searchsorted(t, t_flare))
    k_fin = int(np.searchsorted(t, t_desc + 30.0))                                # established on the final
    fin = slice(k_fin, k_fl)
    path = np.arctan2(d['climb_rate'], np.hypot(d['vn'], d['ve']))
    gear_down = int(np.argmax(d['gear'] >= 0.999))
    rho0 = 1.225
    cas = lambda k: float(d['tas'][k] * math.sqrt(d['rho'][k] / rho0) / KT)
    res = dict(
        what=par['maneuver'], weight_lb=par['condition']['flight_weight_lb'],
        start=dict(speed_kt=d['tas'][0] / KT, altitude_ft=d['height'][0] / FT, alpha_deg=d['alpha'][0] / DEG, throttle=float(d['throttle'][0])),
        gear=dict(commanded_at_s=2.0, down_at_s=float(t[gear_down]), drag_coefficient=float(d['cd_gear'][-1]),
                  drag_at_approach_speed_lbf=float(d['cd_gear'][k_fl] * d['qbar'][k_fl] * par['workspace']['s_ref'] / LBF)),
        base_turn=dict(peak_bank_deg=float(np.abs(d['phi'][:k_fin]).max() / DEG), peak_load_factor_g=float(d['nz'][:k_fin].max()),
                       peak_roll_rate_deg_s=float(np.abs(d['p'][:k_fin]).max() / DEG)),
        final=dict(from_s=float(t[k_fin]), to_s=float(t[k_fl]), speed_kt=float(d['tas'][fin].mean() / KT), speed_calibrated_kt=cas(k_fl),
                   speed_range_kt=[float(d['tas'][fin].min() / KT), float(d['tas'][fin].max() / KT)],
                   path_deg=float(path[fin].mean() / DEG), sink_rate_fpm=float(-d['climb_rate'][fin].mean() / FT * 60),
                   alpha_deg=float(d['alpha'][fin].mean() / DEG), pitch_deg=float(d['theta'][fin].mean() / DEG),
                   stabilator_deg=float(d['stabilator'][fin].mean() / DEG), flap_deg=float(d['flap'][fin].mean() / DEG),
                   throttle=float(d['throttle'][fin].mean()), thrust_lbf=float(d['thrust'][fin].mean() / LBF),
                   lift_coefficient=float(d['cl'][fin].mean()), drag_coefficient=float(d['cd'][fin].mean()), lift_to_drag=float((d['cl'][fin] / d['cd'][fin]).mean()),
                   alpha_limiter_deg=par['workspace']['alpha_lim'] / DEG, margin_to_limiter_deg=float((par['workspace']['alpha_lim'] - d['alpha'][fin].max()) / DEG)),
        flare=dict(start_s=float(t_flare), wheel_height_at_start_ft=float(hw[k_fl] / FT), duration_s=float(t[k_td] - t_flare)),
        touchdown=dict(at_s=float(t[k_td]), reached=bool(hw[k_td] <= 0.0), speed_kt=float(d['tas'][k_td] / KT), sink_rate_ft_s=float(-d['climb_rate'][k_td] / FT),
                       alpha_deg=float(d['alpha'][k_td] / DEG), pitch_deg=float(d['theta'][k_td] / DEG), bank_deg=float(d['phi'][k_td] / DEG),
                       stabilator_deg=float(d['stabilator'][k_td] / DEG), throttle=float(d['throttle'][k_td]),
                       distance_from_flare_start_ft=float(np.hypot(d['pn'][k_td] - d['pn'][k_fl], d['pe'][k_td] - d['pe'][k_fl]) / FT),
                       nose_wheel_clear_ft=float((d['height'][k_td] - (-geo['x_nose'] * math.sin(d['theta'][k_td]) + geo['z'] * math.cos(d['theta'][k_td]))) / FT)),
        geometry=dict(main_wheel_from_cg_body_m=[geo['x'], geo['z']], note='wheel contact from the design inputs (main gear station, ground line 47 in below the reference line); '
                      'the height datum of the run is the runway; the model has no ground: the run ends when the main wheels reach the datum'),
        limits='no ground effect, no ground contact, no wind or turbulence; flap is both flaperons 30 deg down (the notebook geometry has no moving flap)',
        warnings=summ['warnings'], checks=summ['checks'])
    if verify:
        res['python_reference'] = {k: summ['reference'][k] for k in ('worst', 'passed', 'tolerance_relative_to_scale')}
    (RUNS / 'approach' / 'approach.json').write_text(json.dumps(dict(res, t_flare=t_flare, k_touchdown=k_td, wheel=geo), indent=1))
    f, td = res['final'], res['touchdown']
    log(f"  approach: final at {f['speed_kt']:.0f} kt, path {f['path_deg']:.2f} deg, sink {f['sink_rate_fpm']:.0f} ft/min, alpha {f['alpha_deg']:.1f} deg, pitch {f['pitch_deg']:.1f} deg, "
        f"throttle {f['throttle']:.2f}; touchdown at {td['at_s']:.1f} s, {td['speed_kt']:.0f} kt, sink {td['sink_rate_ft_s']:.1f} ft/s, pitch {td['pitch_deg']:.1f} deg")
    return res


def main():
    what = [a for a in sys.argv[1:] if not a.startswith('--')] or ['approach', 'turns']
    verify = '--verify' in sys.argv
    OUT.mkdir(exist_ok=True)
    path = OUT / 'flights.json'
    res = json.loads(path.read_text()) if path.exists() else {}
    if 'approach' in what:
        res['approach'] = fly_approach(verify)
    if 'turns' in what:
        res['turns'] = {c['name']: fly_turn(c, verify) for c in TURNS}
    for name in what:
        for c in TURNS:
            if c['name'] == name:
                res.setdefault('turns', {})[name] = fly_turn(c, verify)
    path.write_text(json.dumps(res, indent=1))
    print(f'wrote {path}')


if __name__ == '__main__':
    main()
