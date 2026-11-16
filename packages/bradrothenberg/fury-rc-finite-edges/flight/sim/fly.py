"""Fly the Fury 6-DOF model by command in the native Unlinked engine, without editing the model.

    python flight/sim/fly.py --schedule flight/sim/schedules/approach.json
    python flight/sim/fly.py --schedule my.json --case combat --mach 0.6 --alt-ft 15000

A schedule file holds time-tagged targets (heading or bank or roll rate; altitude or load factor; Mach or airspeed
or throttle; sideslip; flap; landing gear), see schedule.py for every key. A schedule may carry its own start
condition: "condition": {"case": "landing", "mach": 0.25, "altitude_ft": 1200, "gear": 0, "flap_deg": 0,
"hold_speed": 1, "table_mach": 0.3}. fly.py trims the aircraft there, turns the schedule into the command time
tables of the model, runs the model in the engine and writes into the run folder (default runs/<schedule name>/):

    trace.json      every recorded signal at 1/60 s (SI units) with the schedule and the command tables
    raw.npz         the same at the solver step
    params.json     the complete parameter set of the run (workspace, tables, commands)
    summary.json    what was flown, in US customary units: a line every 5 s, extremes, limiters, warnings

The control laws stay in the loop: the limits on load factor, angle of attack and roll rate apply to every command.
A row that needs the flown state ("hold", or a heading after flying by bank or roll rate) makes fly.py stop the
engine at that time and start it again from the recorded states.

Ported from an earlier flight study by the same author.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

SIM = Path(__file__).resolve().parent
sys.path.insert(0, str(SIM))
sys.path.insert(0, str(SIM / 'verify'))
import params as P  # noqa: E402
import run as runner  # noqa: E402
import schedule as S  # noqa: E402

DEG = math.pi / 180.0
FT, KT, LBF, G0 = 0.3048, 0.514444444, 4.4482216153, 9.80665
MAX_KNOTS = 40          # command breakpoints per engine call (the engine command line has a length limit)

# signals compared with the Python reference, with the scale that makes the difference dimensionless
COMPARE = dict(pn=('m', 1000.0), pe=('m', 1000.0), pd=('m', 100.0), u=('m/s', 100.0), v=('m/s', 10.0), w=('m/s', 10.0),
               p=('rad/s', 1.0), q=('rad/s', 0.2), r=('rad/s', 0.1), e0=('-', 1.0), e1=('-', 1.0), e2=('-', 1.0), e3=('-', 1.0),
               phi=('rad', 1.0), theta=('rad', 0.1), alpha=('rad', 0.2), beta=('rad', 0.05), mach=('-', 0.5), nz=('g', 4.0),
               track_unwrapped=('rad', 3.0), stabilator=('rad', 0.2), flaperon_left=('rad', 0.2), flaperon_right=('rad', 0.2), rudder=('rad', 0.1),
               gear=('-', 1.0), throttle=('-', 1.0), thrust=('N', 1.5e4), spool=('-', 1.0),
               pitch_integrator=('rad', 0.2), throttle_integrator=('-', 1.0), lift=('N', 1.0e5), drag=('N', 2.0e4),
               moment_l=('N m', 1.0e4), moment_m=('N m', 1.0e4), moment_n=('N m', 2.0e3), nz_cmd=('g', 4.0), bank_cmd=('rad', 1.0),
               sustained_nz_integrator=('g', 4.0), nz_thrust_feedforward=('g', 4.0), nz_speed_hold=('g', 4.0), nz_available=('g', 4.0),
               thrust_flag=('-', 1.0), aero_fz=('N', 1.0e5), force_x=('N', 2.0e4), cl=('-', 0.5), cd=('-', 0.1), cm=('-', 0.02),
               u_dot=('m/s2', 5.0), w_dot=('m/s2', 20.0), q_dot=('rad/s2', 0.5), p_dot=('rad/s2', 2.0), r_dot=('rad/s2', 0.2),
               climb_rate_cmd=('m/s', 10.0), roll_rate_cmd=('rad/s', 1.0), airspeed_cmd=('m/s', 100.0))


def diff_table(t, a, b, names=COMPARE):
    out, worst = {}, (0.0, None)
    for n, (unit, scale) in names.items():
        if n not in a or n not in b:
            continue
        e = np.abs(a[n] - b[n])
        k = int(np.argmax(e))
        out[n] = dict(unit=unit, max_abs=float(e[k]), at_t=float(t[k]), relative_to_scale=float(e[k] / scale), scale=scale)
        if e[k] / scale > worst[0]:
            worst = (float(e[k] / scale), n)
    return out, dict(value=worst[0], signal=worst[1])


class Flight:
    """The aircraft in the air: trimmed start, command tables, the trace so far."""

    def __init__(self, par, folder, step=runner.STEP, log=print):
        self.par, self.folder, self.step, self.log = par, Path(folder), step, log
        c = par['condition']
        self.cmd = S.Commands(par['workspace'], c['mach'], c['altitude_m'])
        self.t_done = 0.0
        self.t, self.data = None, None
        self.segments = []
        self.rows = []
        self.t_far_min = 0.0
        self.folder.mkdir(parents=True, exist_ok=True)

    def state(self):
        if self.data is None:
            W, c = self.par['workspace'], self.par['condition']
            return dict(track_rad=W['chi0'], height_m=c['altitude_m'], mach=c['mach'], tas_m_s=c['tas_m_s'])
        d = self.data
        return dict(track_rad=float(d['track_unwrapped'][-1]), height_m=float(d['height'][-1]), mach=float(d['mach'][-1]), tas_m_s=float(d['tas'][-1]))

    def advance(self, t_to):
        """Fly from the end of the trace to t_to with the command tables as they are now."""
        t_to = S.snap(t_to)
        while self.t_done < t_to - 1e-9:
            tab = self.cmd.tables()
            inside = [x for x in tab['t'] if self.t_done + 1e-9 < x < t_to - 1e-9]
            b = t_to if len(inside) <= MAX_KNOTS else S.snap(inside[MAX_KNOTS])
            seg = S.window(tab, self.t_done, b)
            over = runner.state_overrides(self.data) if self.data is not None else None
            k = len(self.segments)
            t_far = runner.far_time(max(b, self.t_far_min), self.step)
            t, d, chk = runner.run_case(self.par, self.folder / 'segments' / f'{k:03d}', step=self.step, stop=b, start=self.t_done,
                                        overrides=over, commands=seg, label=f'fly segment {k}', save=False, t_far=t_far)
            if not chk['structural_pass']:
                self.log(f'  WARNING: structural checks failed in the segment {self.t_done:.2f} to {b:.2f} s: {chk}')
            self.segments.append(dict(start=self.t_done, stop=b, samples=chk['samples'], engine_wall_s=chk['engine_wall_s'],
                                      structural_pass=chk['structural_pass'], breakpoints=len(seg['t'])))
            if self.data is None:
                self.t, self.data = t, d
            else:
                self.t = np.concatenate([self.t, t[1:]])
                self.data = {n: np.concatenate([self.data[n], d[n][1:]]) for n in d}
            self.t_done = b

    def command(self, row, linear=False):
        """One schedule row at its time (not before the end of what has been flown)."""
        row = dict(row)
        row['t'] = max(S.snap(row['t']), self.t_done)
        if self.cmd.needs_state(row) and row['t'] > self.t_done + 1e-9:
            self.advance(row['t'])
        said = self.cmd.add(row, self.state() if abs(row['t'] - self.t_done) < 1e-9 else None, linear)
        self.rows.append(row)
        self.log(f"  t = {row['t']:7.2f} s  " + '; '.join(said))
        return said

    def status(self, k=-1):
        d = self.data
        return (f"t {self.t[k]:6.1f} s | track {math.degrees(d['track_unwrapped'][k]) % 360:5.1f} deg | alt {d['height'][k] / FT:7,.0f} ft | "
                f"{d['tas'][k] / KT:5.1f} kt  Mach {d['mach'][k]:.3f} | {d['nz'][k]:4.2f} g | bank {math.degrees(d['phi'][k]):+5.1f} deg | "
                f"alpha {math.degrees(d['alpha'][k]):4.1f} deg | climb {d['climb_rate'][k] / FT * 60:+6.0f} ft/min | throttle {d['throttle'][k]:.2f} | "
                f"stab {math.degrees(d['stabilator'][k]):+5.1f} deg | gear {d['gear'][k]:.2f} flap {math.degrees(d['flap'][k]):4.1f}")

    def summary(self):
        t, d, W = self.t, self.data, self.par['workspace']
        dt = float(t[1] - t[0])
        lim_hi = d['alpha_margin_g'] < d['nz_error']
        every = np.searchsorted(t, np.arange(0.0, t[-1] + 1e-6, 5.0))
        every = np.unique(np.clip(np.append(every, len(t) - 1), 0, len(t) - 1))
        line = lambda k: dict(t_s=round(float(t[k]), 2), track_deg=round(math.degrees(d['track_unwrapped'][k]) % 360, 1),
                              altitude_ft=round(float(d['height'][k] / FT)), speed_kt=round(float(d['tas'][k] / KT), 1), mach=round(float(d['mach'][k]), 3),
                              load_factor_g=round(float(d['nz'][k]), 2), bank_deg=round(math.degrees(d['phi'][k]), 1),
                              alpha_deg=round(math.degrees(d['alpha'][k]), 2), pitch_deg=round(math.degrees(d['theta'][k]), 2),
                              climb_rate_fpm=round(float(d['climb_rate'][k] / FT * 60)), throttle=round(float(d['throttle'][k]), 3),
                              thrust_lbf=round(float(d['thrust'][k] / LBF)), stabilator_deg=round(math.degrees(d['stabilator'][k]), 2),
                              flap_deg=round(math.degrees(d['flap'][k]), 1), gear=round(float(d['gear'][k]), 2),
                              north_ft=round(float(d['pn'][k] / FT)), east_ft=round(float(d['pe'][k] / FT)))
        a_max = self.par['tables_info']['alpha_cl_max_deg']
        sat = dict(stabilator_position=(d['stabilator'] <= W['stab_min'] * (1 - 1e-6)) | (d['stabilator'] >= W['stab_max'] * (1 - 1e-6)),
                   stabilator_rate=np.abs(d['stabilator_rate']) >= W['surf_rate'] * (1 - 1e-6),
                   flaperon_position=(np.minimum(d['flaperon_left'], d['flaperon_right']) <= W['flp_min'] * (1 - 1e-6))
                   | (np.maximum(d['flaperon_left'], d['flaperon_right']) >= W['flp_max'] * (1 - 1e-6)),
                   flaperon_rate=np.maximum(np.abs(d['flaperon_left_rate']), np.abs(d['flaperon_right_rate'])) >= W['surf_rate'] * (1 - 1e-6),
                   rudder_position=np.abs(d['rudder']) >= W['dr_max'] * (1 - 1e-6), rudder_rate=np.abs(d['rudder_rate']) >= W['dr_rate'] * (1 - 1e-6))
        warn = []
        if float(np.sum(lim_hi) * dt) > 0.5:
            warn.append(f'the angle-of-attack limiter of the pitch law was active for {np.sum(lim_hi) * dt:.1f} s (the command asked for more lift than the limiter allows)')
        for k, v in sat.items():
            if float(np.sum(v) * dt) > 0.2:
                warn.append(f'{k.replace("_", " ")} limit reached for {np.sum(v) * dt:.1f} s')
        if d['alpha'].max() / DEG > a_max:
            warn.append(f'the angle of attack went above the angle of the lift maximum ({d["alpha"].max() / DEG:.1f} against {a_max:.1f} deg): stalled')
        if d['nz'].max() > W['nz_lim'] + 0.05 or d['nz'].min() < W['nz_min'] - 0.05:
            warn.append(f'the load factor left the limits ({d["nz"].min():.2f} to {d["nz"].max():.2f} g)')
        if np.abs(d['beta']).max() / DEG > 15 or d['alpha'].max() / DEG > 40:
            warn.append('departed (sideslip above 15 deg or angle of attack above 40 deg)')
        if not all(np.isfinite(v).all() for v in d.values()):
            warn.append('non-finite values in the trace')
        rng = lambda x, f=1.0, nd=1: [round(float(np.min(x) * f), nd), round(float(np.max(x) * f), nd)]
        return dict(
            name=self.par['name'], case=self.par['case'], maneuver=self.par.get('maneuver'),
            start=dict(mach=self.par['condition']['mach'], altitude_ft=round(self.par['condition']['altitude_ft']),
                       speed_kt=round(self.par['condition']['tas_kt'], 1), weight_lb=round(self.par['condition']['flight_weight_lb'])),
            duration_s=float(t[-1]), units='US customary: ft, kt (true airspeed), lbf, g, deg; converted from the stored SI trace',
            every_5_s=[line(int(k)) for k in every],
            extremes=dict(altitude_ft=rng(d['height'], 1 / FT, 0), speed_kt=rng(d['tas'], 1 / KT), mach=rng(d['mach'], 1, 3), load_factor_g=rng(d['nz'], 1, 2),
                          bank_deg=rng(d['phi'], 1 / DEG), alpha_deg=rng(d['alpha'], 1 / DEG, 2), sideslip_deg=rng(d['beta'], 1 / DEG, 2),
                          roll_rate_deg_s=rng(d['p'], 1 / DEG), climb_rate_fpm=rng(d['climb_rate'], 60 / FT, 0), thrust_lbf=rng(d['thrust'], 1 / LBF, 0),
                          stabilator_deg=rng(d['stabilator'], 1 / DEG, 2), flaperon_deg=rng(np.concatenate([d['flaperon_left'], d['flaperon_right']]), 1 / DEG, 2),
                          rudder_deg=rng(d['rudder'], 1 / DEG, 2)),
            limits=dict(load_factor_g=[W['nz_min'], W['nz_lim']], alpha_limiter_deg=[W['alpha_min'] / DEG, W['alpha_lim'] / DEG],
                        alpha_of_lift_maximum_deg=a_max, roll_rate_command_deg_s=W['p_max'] / DEG),
            limiters=dict(alpha_limiter_s=float(np.sum(lim_hi) * dt),
                          load_factor_command_at_structural_limit_s=float(np.sum(d['nz_cmd'] >= W['nz_lim'] * (1 - 1e-9)) * dt),
                          throttle_full_s=float(np.sum(d['throttle'] >= 0.999) * dt), throttle_idle_s=float(np.sum(d['throttle'] <= W['thr_idle'] * 1.001) * dt)),
            saturation_s={k: float(np.sum(v) * dt) for k, v in sat.items()}, warnings=warn, segments=self.segments, schedule_log=self.cmd.log)

    def finish(self, verify=False, schedule_info=None):
        t, d = self.t, self.data
        n_expect = int(round(t[-1] / self.step)) + 1
        checks = dict(samples=len(t), expected_samples=n_expect, time_end=float(t[-1]),
                      time_coverage=bool(len(t) == n_expect and abs(t[0]) < 1e-12), time_monotonic=bool(np.all(np.diff(t) > 0)),
                      aligned=bool(all(len(v) == len(t) for v in d.values())), finite=bool(all(np.isfinite(v).all() for v in d.values())),
                      quat_norm_max_error=float(np.abs(np.sqrt(d['quat_norm2']) - 1).max()),
                      segments=len(self.segments), segments_structural=bool(all(s['structural_pass'] for s in self.segments)))
        checks['structural_pass'] = bool(checks['time_coverage'] and checks['time_monotonic'] and checks['aligned'] and checks['finite']
                                         and checks['quat_norm_max_error'] < 1e-6 and checks['segments_structural'])
        tables = self.cmd.tables()
        par = dict(self.par, commands=tables)
        np.savez_compressed(self.folder / 'raw.npz', t=t, **d)
        (self.folder / 'params.json').write_text(json.dumps(par, indent=1))
        P.write_m(par, self.folder / 'init.m', t_far=runner.far_time(float(t[-1]), self.step))
        (self.folder / 'schedule.json').write_text(json.dumps(dict(schedule_info or {}, duration_s=float(t[-1]), commands=self.rows), indent=1))
        runner.write_trace(self.folder, t, d, par, self.step, extra=dict(schedule=self.rows, command_tables=tables))
        summ = self.summary()
        summ['checks'] = checks
        if verify:
            from ref6dof import Model
            t0 = time.time()
            t4, ref = Model(par).simulate_rk4(float(t[-1]), self.step)
            tab, worst = diff_table(t4, d, ref)
            summ['reference'] = dict(what='the same flight in the independent Python implementation (verify/ref6dof.py), classical RK4 at the same step, '
                                          'one piece from start to end with the complete command tables',
                                     worst=worst, tolerance_relative_to_scale=1e-6, passed=bool(worst['value'] < 1e-6), wall_s=time.time() - t0, signals=tab)
            self.log(f"  Python reference (same RK4 step): worst difference {worst['value']:.1e} of scale ({worst['signal']}) -> "
                     f"{'pass' if summ['reference']['passed'] else 'FAIL'}")
        (self.folder / 'summary.json').write_text(json.dumps(summ, indent=1))
        return summ


def fly_schedule(par, sched, folder, stop=None, verify=False, log=print):
    fl = Flight(par, folder, log=log)
    duration = S.snap(stop or sched['duration_s'])
    fl.t_far_min = duration
    for row in sched['commands']:
        if float(row['t']) > duration:
            log(f"  row at t = {row['t']} s lies after the end of the run ({duration} s): not flown")
            continue
        fl.command(row, linear=sched.get('linear', False))
    fl.advance(duration)
    return fl, fl.finish(verify, dict(description=sched.get('description', ''), condition=sched.get('condition')))


def start(case='combat', mach=0.6, altitude_ft=15000.0, gear=0.0, flap_deg=0.0, hold_speed=1.0, table_mach=None, maneuver='flown by command', log=print):
    par = P.build(case, mach, altitude_ft * FT, gear=gear, flap_deg=flap_deg, hold_speed=hold_speed, table_mach=table_mach, maneuver=maneuver)
    tr = par['trim']
    log(f"{par['name']}: trimmed at Mach {mach:.3f}, {altitude_ft:,.0f} ft, {tr['us_customary']['speed_kt']} kt true, {tr['us_customary']['weight_lb']:,} lb: "
        f"angle of attack {tr['alpha_deg']:.2f} deg, stabilator {tr['stabilator_deg']:.2f} deg, throttle {tr['throttle']:.2f}")
    if not tr['ok']:
        raise SystemExit(f'no trimmed level flight at this start condition: {tr["why_not"]}')
    return par


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--schedule', required=True, help='schedule file (.json or .csv), see schedule.py')
    ap.add_argument('--case', help='weight case: combat, landing, takeoff, light')
    ap.add_argument('--alt-ft', type=float)
    ap.add_argument('--mach', type=float)
    ap.add_argument('--stop', type=float, help='end of the run, s (default: duration_s of the schedule)')
    ap.add_argument('--out', help='run folder (default runs/<schedule name>)')
    ap.add_argument('--verify', action='store_true', help='also fly the same commands in the Python reference model and compare')
    a = ap.parse_args()
    sched = S.read(a.schedule)
    c = dict(case='combat', mach=0.6, altitude_ft=15000.0)
    c.update(sched.get('condition') or {})
    c.update({k: v for k, v in dict(case=a.case, mach=a.mach, altitude_ft=a.alt_ft).items() if v is not None})
    name = Path(a.schedule).stem
    par = start(maneuver=f"{name}: {sched['description']}", **c)
    folder = Path(a.out or SIM / 'runs' / name)
    fl, summ = fly_schedule(par, sched, folder, a.stop, a.verify)
    print('   ' + '\n   '.join(fl.status(int(k)) for k in np.unique(np.clip(np.searchsorted(fl.t, np.arange(0.0, fl.t[-1] + 1e-6, 5.0)), 0, len(fl.t) - 1))))
    print('   ' + fl.status())
    for wmsg in summ['warnings']:
        print('  NOTE: ' + wmsg)
    print(f"  structural checks {'pass' if summ['checks']['structural_pass'] else 'FAIL'}; {len(fl.segments)} engine call(s), "
          f"{sum(s['engine_wall_s'] for s in fl.segments):.1f} s; results in {folder}")
    if not summ['checks']['structural_pass']:
        sys.exit(1)


if __name__ == '__main__':
    main()
