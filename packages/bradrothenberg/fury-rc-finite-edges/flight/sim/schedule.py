"""Command schedules: time-tagged targets a person writes, turned into the command time tables of the model.

Carried over from an earlier flight study by the same author with two more channels: flap and landing gear.

The model reads 17 command tables over one time vector (model/variables.json "schedules"). This module keeps them
as breakpoint lists per channel, adds the rows of a schedule file one at a time, and writes the workspace vectors.

Schedule file, JSON:

    {"description": "...", "duration_s": 120,
     "commands": [ {"t": 5, "heading_change_deg": 90, "bank_limit_deg": 45},
                   {"t": 5, "altitude_ft": 17000, "climb_rate_fpm": 3000},
                   {"t": 60, "mach": 0.55} ]}

or CSV with a header line: t, then any of the keys below; an empty cell means "no change". A line "# interp: linear"
before the header makes every value move in a straight line from the row before (stick time histories).

Keys of a row (US customary units; `t` in seconds from the start of the run):

  lateral   heading_deg          track target as a compass heading of the ground track, 0 = north (the start heading), turned
                                 the short way unless "turn": "left" | "right" is given
            heading_change_deg   track target relative to the present target (positive to the right), any size
            bank_deg             bank angle target, positive right wing down (leaves the track hold)
            roll_rate_dps        roll rate command, the roll stick (leaves the track hold and the bank hold)
            bank_limit_deg       bank allowed in a turn to a track target (default 45), or
            turn_g               load factor allowed in such a turn, or
            max_turn             true: turn at the most the aircraft sustains (limits: thrust, lift, structure)
  vertical  altitude_ft          height target
            climb_rate_fpm       climb and descent rate allowed on the way to a height target (default 3000)
            load_factor_g        load factor command, the pitch stick (leaves the height hold)
  speed     mach                 Mach number target
            speed_kt             true airspeed target, knots
            throttle             throttle lever 0..1 (leaves the speed hold)
  yaw       sideslip_deg         sideslip target, the pedal (positive: nose left of the airflow, wind from the right)
  config    flap_deg             flap command: both flaperons trailing edge down by this angle
            gear                 landing gear: "down" or "up" (or 1 / 0); the gear travels at its own rate
  any       ramp_s               time over which the targets of this row move from the old to the new value (default 1 s;
                                 "from_previous": in a straight line from the previous change of that channel)
            "hold"               as the value of heading_deg, altitude_ft, mach or speed_kt: the value flown at that time

A row that gives a lateral, vertical or speed key selects that way of flying the axis; the other axes stay as they are.
The control laws stay in the loop in every mode: load factor, angle of attack and roll rate limits apply to stick commands too.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

DEG = math.pi / 180.0
FT, KT, FPM = 0.3048, 0.514444444, 0.3048 / 60.0
GRID = 1.0 / 60.0                 # breakpoints are placed on the output grid of the trace
MODE_RAMP = 0.5                   # s, blend between two ways of flying an axis
DEFAULT_RAMP = 1.0                # s
CHANNELS = ('chi', 'phi', 'p', 'sel_bank', 'sel_rate', 'n_turn', 'h', 'vs_max', 'nz', 'sel_nz', 'mach', 'tas', 'thr', 'sel_thr', 'beta', 'flap', 'gear')
VAR = {k: 'sch_' + k for k in CHANNELS}
DEFAULT_BANK_LIMIT_DEG = 45.0
DEFAULT_CLIMB_FPM = 3000.0
KEYS = ('t', 'heading_deg', 'heading_change_deg', 'turn', 'bank_deg', 'roll_rate_dps', 'bank_limit_deg', 'turn_g', 'max_turn', 'altitude_ft',
        'climb_rate_fpm', 'load_factor_g', 'mach', 'speed_kt', 'throttle', 'sideslip_deg', 'flap_deg', 'gear', 'ramp_s', 'note')
NEEDS_STATE_IF_HOLD = ('heading_deg', 'altitude_ft', 'mach', 'speed_kt')


def snap(t):
    return round(float(t) / GRID) * GRID


class Commands:
    """Breakpoint lists per channel. `values` at t = 0 are the trimmed entry condition."""

    def __init__(self, workspace, mach, h_m, n_turn=None, vs_max=None):
        W = workspace
        n_turn = (1.0 / math.cos(DEFAULT_BANK_LIMIT_DEG * DEG)) if n_turn is None else n_turn
        start = dict(chi=W.get('chi0', 0.0), phi=0.0, p=0.0, sel_bank=0.0, sel_rate=0.0, n_turn=n_turn, h=h_m,
                     vs_max=DEFAULT_CLIMB_FPM * FPM if vs_max is None else vs_max, nz=1.0, sel_nz=0.0, mach=mach, tas=0.0,
                     thr=W.get('thr0', 0.5), sel_thr=0.0, beta=0.0, flap=0.5 * (W.get('dfl0', 0.0) + W.get('dfr0', 0.0)), gear=W.get('gear0', 0.0))
        self.bp = {k: [(0.0, float(start[k]))] for k in CHANNELS}
        self.nz_lim = W['nz_lim']
        self.lateral, self.vertical, self.speed = 'track', 'height', 'speed'
        self.log = []

    # ---- breakpoints
    def value(self, k, t):
        ts, ys = zip(*self.bp[k])
        return float(np.interp(t, ts, ys))

    def move(self, k, t, new, ramp):
        """Channel k goes from its value at t to `new` over `ramp` seconds (ramp None: straight line from its last breakpoint)."""
        t = snap(t)
        bp = self.bp[k]
        if ramp is None:
            if bp[-1][0] >= t:
                raise ValueError(f'{k}: a straight-line row at t = {t:.3f} s lies before the previous change of that channel')
            bp.append((t, float(new)))
            return
        ramp = max(snap(ramp), GRID)
        now = self.value(k, t)
        while bp and bp[-1][0] > t - 1e-9:           # a ramp still under way is cut at t
            bp.pop()
        bp.append((t if bp else 0.0, now))
        bp.append((t + ramp, float(new)))

    # ---- one row of a schedule
    def needs_state(self, row):
        if any(row.get(k) == 'hold' for k in NEEDS_STATE_IF_HOLD):
            return True
        return self.lateral != 'track' and (row.get('heading_deg') is not None or row.get('heading_change_deg') is not None)

    def add(self, row, state=None, linear=False):
        """state: dict(track_rad, height_m, mach, tas_m_s) of the aircraft at row['t'], needed when needs_state(row)."""
        unknown = [k for k in row if k not in KEYS]
        if unknown:
            raise ValueError(f'unknown key(s) {unknown} in schedule row {row}; known: {KEYS}')
        t = float(row['t'])
        ramp = row.get('ramp_s', None if linear else DEFAULT_RAMP)
        ramp = None if ramp == 'from_previous' else ramp
        mode_ramp = MODE_RAMP if ramp is None else min(MODE_RAMP, max(float(ramp), GRID))
        has = lambda k: row.get(k) is not None and row.get(k) != ''
        said = []

        def need(what):
            if state is None:
                raise ValueError(f'row at t = {t} needs the flown {what}; run the schedule through fly.py')
            return state

        # lateral
        if has('heading_deg') or has('heading_change_deg'):
            base = self.value('chi', t) if self.lateral == 'track' else need('track')['track_rad']
            if has('heading_change_deg'):
                target = base + float(row['heading_change_deg']) * DEG
            elif row['heading_deg'] == 'hold':
                target = need('track')['track_rad']
            else:
                d = (float(row['heading_deg']) * DEG - base + math.pi) % (2 * math.pi) - math.pi      # the short way
                turn = row.get('turn')
                if turn == 'right' and d < 0:
                    d += 2 * math.pi
                if turn == 'left' and d > 0:
                    d -= 2 * math.pi
                target = base + d
            if self.lateral != 'track':                  # the table is set to the flown track first, then moved
                self.move('chi', t, base, GRID)
                self.move('chi', t + GRID, target, max(float(ramp or DEFAULT_RAMP) - GRID, GRID))
            else:
                self.move('chi', t, target, ramp)
            self.move('sel_bank', t, 0.0, mode_ramp); self.move('sel_rate', t, 0.0, mode_ramp)
            self.lateral = 'track'
            said.append(f'track target {math.degrees(target) % 360:.1f} deg ({math.degrees(target - base):+.1f} deg)')
        if has('bank_deg'):
            self.move('phi', t, float(row['bank_deg']) * DEG, ramp)
            self.move('sel_bank', t, 1.0, mode_ramp); self.move('sel_rate', t, 0.0, mode_ramp)
            self.lateral = 'bank'
            said.append(f'bank {float(row["bank_deg"]):+.1f} deg')
        if has('roll_rate_dps'):
            self.move('p', t, float(row['roll_rate_dps']) * DEG, ramp)
            self.move('sel_rate', t, 1.0, mode_ramp)
            self.lateral = 'roll rate'
            said.append(f'roll rate {float(row["roll_rate_dps"]):+.1f} deg/s')
        if has('max_turn') and str(row['max_turn']).lower() not in ('0', 'false', 'no'):
            self.move('n_turn', t, self.nz_lim, mode_ramp); said.append('turn limit: the most the aircraft sustains')
        elif has('turn_g'):
            self.move('n_turn', t, float(row['turn_g']), mode_ramp); said.append(f'turn limit {float(row["turn_g"]):.2f} g')
        elif has('bank_limit_deg'):
            b = min(abs(float(row['bank_limit_deg'])), 85.0)
            self.move('n_turn', t, 1.0 / math.cos(b * DEG), mode_ramp); said.append(f'turn limit {b:.0f} deg of bank')
        # vertical
        if has('altitude_ft'):
            h = need('height')['height_m'] if row['altitude_ft'] == 'hold' else float(row['altitude_ft']) * FT
            if self.vertical != 'height':
                self.move('h', t, h, GRID)
            else:
                self.move('h', t, h, ramp)
            self.move('sel_nz', t, 0.0, mode_ramp)
            self.vertical = 'height'
            said.append(f'height target {h / FT:,.0f} ft')
        if has('climb_rate_fpm'):
            self.move('vs_max', t, abs(float(row['climb_rate_fpm'])) * FPM, mode_ramp); said.append(f'climb rate limit {abs(float(row["climb_rate_fpm"])):,.0f} ft/min')
        if has('load_factor_g'):
            self.move('nz', t, float(row['load_factor_g']), ramp)
            self.move('sel_nz', t, 1.0, mode_ramp)
            self.vertical = 'load factor'
            said.append(f'load factor {float(row["load_factor_g"]):.2f} g')
        # speed
        if has('mach') or has('speed_kt'):
            if has('mach'):
                m = need('Mach number')['mach'] if row['mach'] == 'hold' else float(row['mach'])
                self.move('mach', t, m, ramp); self.move('tas', t, 0.0, ramp); said.append(f'Mach target {m:.3f}')
            else:
                v = need('airspeed')['tas_m_s'] if row['speed_kt'] == 'hold' else float(row['speed_kt']) * KT
                self.move('tas', t, v, ramp); self.move('mach', t, 0.0, ramp); said.append(f'airspeed target {v / KT:.0f} kt true')
            self.move('sel_thr', t, 0.0, mode_ramp)
            self.speed = 'speed'
        if has('throttle'):
            self.move('thr', t, min(max(float(row['throttle']), 0.0), 1.0), ramp)
            self.move('sel_thr', t, 1.0, mode_ramp)
            self.speed = 'throttle'
            said.append(f'throttle {float(row["throttle"]):.2f}')
        if has('sideslip_deg'):
            self.move('beta', t, float(row['sideslip_deg']) * DEG, ramp); said.append(f'sideslip target {float(row["sideslip_deg"]):+.1f} deg')
        if has('flap_deg'):
            self.move('flap', t, float(row['flap_deg']) * DEG, ramp); said.append(f'flap {float(row["flap_deg"]):.0f} deg')
        if has('gear'):
            down = str(row['gear']).lower() in ('down', '1', '1.0', 'true')
            self.move('gear', t, 1.0 if down else 0.0, mode_ramp); said.append('landing gear ' + ('down' if down else 'up'))
        self.log.append(dict(t=t, said=said, row=row))
        return said

    # ---- tables for the model
    def tables(self):
        """dict(t=[...], <channel>=[...]) on the union of all breakpoint times."""
        ts = sorted({round(t / GRID) for bp in self.bp.values() for t, _ in bp} | {0})
        t = [k * GRID for k in ts]
        if len(t) < 2:
            t.append(GRID)
        out = dict(t=t)
        for k in CHANNELS:
            a, y = zip(*self.bp[k])
            out[k] = [float(v) for v in np.interp(t, a, y)]
        return out


def constant(workspace, mach, h_m, n_turn=None):
    """Command tables that hold the entry condition (the study maneuver adds its track step with t_turn, chi_turn)."""
    return Commands(workspace, mach, h_m, n_turn=n_turn).tables()


def workspace_vectors(tables, t_far):
    """The tables as the workspace expressions the engine takes: every vector ends at t_far with its last value."""
    t = list(tables['t'])
    assert t[0] == 0.0 and t_far > t[-1] + 1e-9, 'the far end of the command tables must lie after the last breakpoint'
    fmt = lambda a: '[' + ' '.join(repr(float(x)) for x in a) + ']'
    out = {'sch_t': fmt(t + [t_far])}
    for k in CHANNELS:
        out[VAR[k]] = fmt(list(tables[k]) + [tables[k][-1]])
    return out


def read(path):
    """Schedule file -> dict(description, duration_s, linear, commands sorted by time)."""
    path = Path(path)
    if path.suffix.lower() == '.json':
        s = json.loads(path.read_text())
        rows = [dict(r) for r in s['commands']]
        out = dict(description=s.get('description', ''), duration_s=s.get('duration_s'), linear=bool(s.get('interp') == 'linear'),
                   condition=s.get('condition'))
    else:
        lines = path.read_text().splitlines()
        meta = [ln[1:].strip() for ln in lines if ln.startswith('#')]
        body = [ln for ln in lines if ln.strip() and not ln.startswith('#')]
        rows = []
        for r in csv.DictReader(body):
            row = {}
            for k, v in r.items():
                k, v = k.strip(), (v or '').strip()
                if v == '':
                    continue
                if k in ('turn', 'note', 'gear') or v in ('hold', 'from_previous'):
                    row[k] = v
                elif k == 'max_turn':
                    row[k] = v.lower() in ('1', 'true', 'yes')
                else:
                    row[k] = float(v)
            rows.append(row)
        get = lambda name: next((m.split(':', 1)[1].strip() for m in meta if m.lower().startswith(name + ':')), None)
        out = dict(description=get('description') or '', duration_s=float(get('duration_s')) if get('duration_s') else None,
                   linear=(get('interp') == 'linear'), condition=None)
    for r in rows:
        if 't' not in r:
            raise ValueError(f'schedule row without a time: {r}')
    rows.sort(key=lambda r: float(r['t']))             # stable: rows of one time keep their order
    out['commands'] = rows
    if out['duration_s'] is None:
        out['duration_s'] = float(rows[-1]['t']) + 30.0 if rows else 30.0
    return out


def window(tables, a, b):
    """The same tables cut to the part a run from a to b reads: breakpoints at 0 (holding the value at a), a, those inside (a, b) and b.
    Keeps the engine command short for long schedules; the values between a and b are unchanged."""
    t = np.asarray(tables['t'], float)
    inside = [float(x) for x in t if a + 1e-9 < x < b - 1e-9]
    ts = ([0.0] if a > 1e-9 else []) + [float(a)] + inside + [float(b)]
    out = dict(t=ts)
    for k in CHANNELS:
        y = np.interp(ts, t, tables[k])
        if a > 1e-9:
            y[0] = y[1]
        out[k] = [float(v) for v in y]
    return out
