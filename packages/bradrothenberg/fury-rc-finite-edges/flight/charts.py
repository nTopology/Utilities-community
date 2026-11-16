"""Charts of the Fury flight study (PNG, flight/out/): turn rate and excess power against an F-16C, and the 6-DOF flights.

    python flight/charts.py

Reads flight/out/turn.json (point performance), flight/out/flights.json and the 6-DOF traces flight/sim/runs/*/raw.npz
(or trace_30hz.npz, the reduced copy that ships with the published package).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

FLIGHT = Path(__file__).resolve().parent
OUT = FLIGHT / 'out'
RUNS = FLIGHT / 'sim' / 'runs'
DEG, FT, KT, G0 = math.pi / 180.0, 0.3048, 0.514444444, 9.80665

SURFACE, INK, INK2, MUTED, GRID, AXIS = '#fcfcfb', '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7'
BLUE, ORANGE = '#2a78d6', '#eb6834'          # categorical slots 1 and 2: Fury, F-16 (fixed)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': AXIS, 'axes.labelcolor': INK2, 'text.color': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.facecolor': SURFACE, 'figure.facecolor': SURFACE, 'savefig.facecolor': SURFACE,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.8, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titlesize': 11, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left', 'legend.frameon': False})


def style(ax):
    ax.tick_params(length=0)
    ax.set_axisbelow(True)


def turn_rate_chart(T):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.6), sharey=True)
    for ax, alt in zip(axes, ('0', '15000')):
        A = T['by_altitude'][alt]
        for key, col, name in (('fury', BLUE, 'Fury model'), ('f16_ab', ORANGE, 'F-16C, afterburner')):
            env = A[key]['envelope']
            v = np.array([e['speed_kt'] for e in env])
            ri = np.array([e.get('rate_inst') if e.get('rate_inst') is not None else np.nan for e in env], float)
            rs = np.array([e.get('rate_sust') if e.get('rate_sust') is not None else np.nan for e in env], float)
            ax.plot(v, ri, color=col, lw=2, label=f'{name}: most it can pull (speed falls)')
            ax.plot(v, rs, color=col, lw=2, ls=(0, (5, 2.5)), label=f'{name}: sustained on thrust')
            # the tightest turn at 9 g and at 5 g
            for row in A[key]['g']:
                if row['n'] in (9.0, 5.0) and row['available']:
                    ax.plot(row['speed_kt'], row['rate_deg_s'], 'o', ms=8, color=col, mec=SURFACE, mew=2, zorder=5)
                    r10 = round(row['radius_ft'], -1)
                    if key == 'fury':
                        ax.annotate(f"{row['n']:.0f} g\n{r10:,.0f} ft", (row['speed_kt'], row['rate_deg_s']), xytext=(-10, 4), textcoords='offset points',
                                    ha='right', fontsize=9, color=INK2)
                    else:
                        off = (12, 9) if row['n'] == 9.0 else (13, -15)
                        ax.annotate(f"{row['n']:.0f} g, {r10:,.0f} ft", (row['speed_kt'], row['rate_deg_s']), xytext=off, textcoords='offset points',
                                    ha='left', fontsize=9, color=INK2)
        ax.set_title('Sea level' if alt == '0' else '15,000 ft')
        ax.set_xlabel('True airspeed [kt]')
        ax.set_xlim(100, 640); ax.set_ylim(0, 32)
        style(ax)
    axes[0].set_ylabel('Turn rate [deg/s]')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=2, fontsize=9.5, bbox_to_anchor=(0.5, -0.005), handlelength=3.2)
    fig.suptitle('Level turn rate: the Fury model out-turns the F-16 for a moment, the F-16 keeps its turn going', x=0.012, ha='left', fontsize=13, fontweight='bold')
    fig.text(0.012, 0.915, 'Both at half internal fuel with two missiles. Dots: the tightest turn at 9 g and at 5 g (radius). Estimates; see flight/out/turn.md.', fontsize=9.5, color=INK2)
    fig.tight_layout(rect=(0, 0.075, 1, 0.9))
    fig.savefig(OUT / 'turn_rate.png', dpi=170)
    plt.close(fig)


def excess_power_chart(T):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), sharey=True)
    for ax, alt in zip(axes, ('0', '15000')):
        A = T['by_altitude'][alt]
        for key, col, name, ls in (('fury', BLUE, 'Fury model', '-'), ('f16_ab', ORANGE, 'F-16C, afterburner', '-'), ('f16_mil', ORANGE, 'F-16C, military power', (0, (5, 2.5)))):
            env = [e for e in A[key]['envelope'] if e.get('ps_1g_ft_s') is not None]
            v = np.array([e['speed_kt'] for e in env]); ps = np.array([e['ps_1g_ft_s'] for e in env])
            ok = ps > -50
            ax.plot(v[ok], ps[ok], color=col, lw=2, ls=ls, label=name)
            k = int(np.argmax(ps))
            below = key == 'fury'
            ax.annotate(f'{name}\npeak {ps[k]:,.0f} ft/s', (v[k], ps[k]), xytext=(0, -9 if below else 7), textcoords='offset points', ha='center',
                        va='top' if below else 'bottom', fontsize=9, color=INK2)
        ax.axhline(0, color=AXIS, lw=1)
        ax.set_title('Sea level' if alt == '0' else '15,000 ft')
        ax.set_xlabel('True airspeed [kt]')
        ax.set_xlim(100, 640); ax.set_ylim(0, 1250)
        style(ax)
    axes[0].set_ylabel('Excess power at 1 g, full thrust [ft/s]')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, fontsize=9.5, bbox_to_anchor=(0.5, -0.005), handlelength=3.2)
    fig.suptitle('Power coming out of the turn: what is left to climb or accelerate with at 1 g', x=0.012, ha='left', fontsize=13, fontweight='bold')
    fig.text(0.012, 0.905, 'Specific excess power = rate of climb available at constant speed. Estimates; see flight/out/turn.md.', fontsize=9.5, color=INK2)
    fig.tight_layout(rect=(0, 0.075, 1, 0.89))
    fig.savefig(OUT / 'excess_power.png', dpi=170)
    plt.close(fig)


def load_trace(folder):
    """Recorded signals of a run: raw.npz (every solver step) or, in the published package, trace_30hz.npz (every eighth step)."""
    f = folder / 'raw.npz'
    return np.load(f if f.exists() else folder / 'trace_30hz.npz')


def turn_trace_chart(name, title):
    z = load_trace(RUNS / name)
    t = z['t']
    ps = (z['climb_rate'] + z['tas'] * np.gradient(z['tas'], t) / G0) / FT
    k = np.ones(120) / 120
    ps = np.convolve(ps, k, mode='same')
    fig = plt.figure(figsize=(12.5, 6.4))
    gs = fig.add_gridspec(3, 2, width_ratios=(1.0, 1.25), hspace=0.32, wspace=0.2)
    axg = fig.add_subplot(gs[:, 0])
    axg.plot(z['pe'] / FT, z['pn'] / FT, color=BLUE, lw=2)
    for ts in np.arange(0, t[-1] + 1e-6, 5.0):
        i = int(np.searchsorted(t, ts))
        if i < len(t):
            axg.plot(z['pe'][i] / FT, z['pn'][i] / FT, 'o', ms=5, color=BLUE, mec=SURFACE, mew=1.2)
            axg.annotate(f'{ts:.0f} s', (z['pe'][i] / FT, z['pn'][i] / FT), xytext=(6, 4), textcoords='offset points', fontsize=8.5, color=INK2)
    axg.set_aspect('equal', adjustable='datalim')
    axg.set_xlabel('East [ft]'); axg.set_ylabel('North [ft]'); axg.set_title('Ground track (a dot every 5 s)')
    style(axg)
    rows = (('Load factor [g]', z['nz'], None), ('True airspeed [kt]', z['tas'] / KT, None), ('Excess power [ft/s]', ps, 0.0))
    for i, (lab, y, zero) in enumerate(rows):
        ax = fig.add_subplot(gs[i, 1])
        ax.plot(t, y, color=BLUE, lw=2)
        if zero is not None:
            ax.axhline(zero, color=AXIS, lw=1)
        if i == 0:
            ax.plot(t, z['nz_cmd'], color=MUTED, lw=1.2, ls=(0, (4, 2)))
            ax.annotate('commanded', (t[len(t) // 3], z['nz_cmd'][len(t) // 3]), xytext=(4, 6), textcoords='offset points', fontsize=8.5, color=MUTED)
        ax.set_title(lab, fontsize=10)
        if i == 2:
            ax.set_xlabel('Time [s]')
        else:
            ax.tick_params(labelbottom=False)
        ax.set_xlim(0, t[-1])
        style(ax)
    fig.suptitle(title, x=0.012, ha='left', fontsize=13, fontweight='bold')
    fig.text(0.012, 0.925, 'Fury model, 6,730 lb, flown in the Unlinked engine by the flight control laws of the block graph. Estimates.', fontsize=9.5, color=INK2)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.86, bottom=0.08)
    fig.savefig(OUT / f'{name}.png', dpi=170)
    plt.close(fig)


def approach_chart():
    z = load_trace(RUNS / 'approach')
    info = json.loads((RUNS / 'approach' / 'approach.json').read_text())
    t = z['t']
    k_td = int(np.argmin(np.abs(z['t'] - info['touchdown']['at_s'])))
    sl = slice(0, k_td + 1)
    t = t[sl]
    geo = info['wheel']
    half = 67.5 * 0.0254 / 2
    th, ph = z['theta'][sl], z['phi'][sl]
    down = lambda y: -geo['x'] * np.sin(th) + y * np.sin(ph) * np.cos(th) + geo['z'] * np.cos(ph) * np.cos(th)
    hw = (z['height'][sl] - np.maximum(down(half), down(-half))) / FT
    fig, axes = plt.subplots(4, 1, figsize=(12.5, 8.6), sharex=True)
    panels = (
        ('Main wheel height above the runway [ft]', [(hw, BLUE, '-', None)]),
        ('True airspeed [kt]', [(z['tas'][sl] / KT, BLUE, '-', None)]),
        ('Angle of attack and pitch attitude [deg]', [(z['alpha'][sl] / DEG, BLUE, '-', 'angle of attack'), (z['theta'][sl] / DEG, ORANGE, '-', 'pitch attitude')]),
        ('Bank angle [deg]', [(z['phi'][sl] / DEG, BLUE, '-', None)]),
    )
    for ax, (lab, lines) in zip(axes, panels):
        for y, col, ls, name in lines:
            ax.plot(t, y, color=col, lw=2, ls=ls, label=name)
            if name:
                i = int(len(t) * 0.55)
                ax.annotate(name, (t[i], y[i]), xytext=(0, 7), textcoords='offset points', fontsize=9, color=INK2)
        ax.set_title(lab, fontsize=10)
        style(ax)
    axes[2].legend(loc='upper left', ncol=2, fontsize=9)
    ev = [(2.0, 'gear down'), (4.0, 'base turn'), (6.0, 'flap 30 deg,\nslow to 110 kt'), (45.0, '3 deg final'), (info['t_flare'], 'flare')]
    top = axes[0].get_ylim()[1]
    for k, (te, lab) in enumerate(ev):
        for ax in axes:
            ax.axvline(te, color=AXIS, lw=1, zorder=0)
        axes[0].annotate(lab, (te, top), xytext=(4, -4 - 22 * (k % 3 if te < 10 else 0)), textcoords='offset points', va='top', fontsize=8.5, color=INK2)
    axes[-1].set_xlabel('Time [s]')
    axes[-1].set_xlim(0, t[-1] + 1)
    td = info['touchdown']
    fig.suptitle('Landing approach with the gear down: base turn, 3 deg final at 110 kt, flare to touchdown', x=0.012, ha='left', fontsize=13, fontweight='bold')
    fig.text(0.012, 0.945, f"Fury model at {info['weight_lb']:,.0f} lb. Touchdown at {td['speed_kt']:.0f} kt, sink {td['sink_rate_ft_s']:.1f} ft/s, pitch {td['pitch_deg']:.1f} deg. "
             'Flown in the Unlinked engine; no ground effect or ground contact in the model. Estimates.', fontsize=9.5, color=INK2)
    fig.subplots_adjust(left=0.06, right=0.985, top=0.9, bottom=0.06, hspace=0.3)
    fig.savefig(OUT / 'approach.png', dpi=170)
    plt.close(fig)


def main():
    T = json.loads((OUT / 'turn.json').read_text())
    turn_rate_chart(T)
    excess_power_chart(T)
    if (RUNS / 'turn_9g_360_sl' / 'summary.json').exists():
        turn_trace_chart('turn_9g_360_sl', '9 g turn through 360 deg from Mach 0.70 near sea level: speed bleeds until the lift limit sets the turn')
    if (RUNS / 'turn_5g_sl' / 'summary.json').exists():
        turn_trace_chart('turn_5g_sl', '5 g turn through 360 deg at Mach 0.60 near sea level: held on thrust')
    if (RUNS / 'approach' / 'approach.json').exists():
        approach_chart()
    print('charts written to', OUT)


if __name__ == '__main__':
    main()
