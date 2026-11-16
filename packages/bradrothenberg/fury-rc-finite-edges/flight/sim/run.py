"""Run the 6-DOF model in the native Unlinked engine and keep the result.

The engine is the command-line program of Unlinked (https://github.com/CosmicFrontierLabs/unlinked, Apache-2.0), `sim`
subcommand, built with `cargo build --release`. No backend service is involved. Python does not integrate anything here.
Where the program is: the environment variable UNLINKED_EXE, or the one line of the file .local/unlinked_exe.txt in the
project folder, or `unlinked` on the PATH. The engine must accept `--signal` (output selection).
Ported from an earlier flight study by the same author.

    python run.py params/<revision>/<file>.json [--out folder] [--stop 90] [--step 0.0041666] [--blocks]

Per run: request.json (model and engine hashes, effective workspace, command), engine.log, raw.npz (every
recorded signal at the solver step), trace.json (fixed output step of 1/60 s), checks.json (terminal status,
time coverage, finite values, aligned arrays, invariants).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

SIM = Path(__file__).resolve().parent
sys.path.insert(0, str(SIM))
import schedule  # noqa: E402


def engine():
    """Path of the Unlinked command-line program (see the top of this file for where it is looked up)."""
    note = SIM.parents[1] / '.local' / 'unlinked_exe.txt'
    cand = os.environ.get('UNLINKED_EXE') or (note.read_text().strip() if note.exists() else '') or shutil.which('unlinked')
    if not cand or not Path(cand).exists():
        raise SystemExit('The Unlinked command-line program was not found. Build it as described in flight/README.md ("The engine": a checkout of '
                         'https://github.com/CosmicFrontierLabs/unlinked with flight/sim/unlinked_signal_option.patch, cargo build --release) '
                         'and set UNLINKED_EXE to target/release/unlinked[.exe].')
    return Path(cand)


MODEL = SIM / 'model/fury_6dof.mdl'
STEP = 1 / 240          # solver step, s (RK4)
STOP = 30.0             # s
OUT_HZ = 60             # trace.json output rate
BUDGET = 9_500_000      # values per engine call (the engine refuses more than 10 million)
FAR_S = 60.0            # the command tables end this long after the end of the run (they must not repeat inside it)
MAX_COMMAND_CHARS = 30000


def engine_commit():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=engine().parent, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception as e:      # noqa: BLE001
        return f'unknown ({e})'


def far_time(stop, step):
    """End of the command tables: a whole number of solver steps, after the end of the run."""
    return (int(round(stop / step)) + int(round(FAR_S / step))) * step


def call_engine(workspace, commands, folder, signal_ids, step, stop, start=0.0, tag='raw', timeout=1800, t_far=None):
    """One engine call. Returns (time array, {signal id: array}, info)."""
    folder.mkdir(parents=True, exist_ok=True)
    n = int(round((stop - start) / step)) + 1
    assert len(signal_ids) * n <= BUDGET, 'too many values for one engine call'
    out = folder / f'{tag}.json'
    cmd = [str(engine()), 'sim', str(MODEL), '--start', repr(float(start)), '--stop', repr(float(stop)), '--step', repr(float(step)), '--solver', 'rk4',
           '--max-samples', str(n + 1), '-o', str(out)]
    for k, v in workspace.items():
        cmd += ['--var', f'{k}={float(v)!r}']
    vectors = schedule.workspace_vectors(commands, far_time(stop, step) if t_far is None else t_far)
    for k, v in vectors.items():
        cmd += ['--var', f'{k}={v}']
    for sid in signal_ids:
        cmd += ['--signal', sid]
    size = sum(len(c) + 3 for c in cmd)
    if size > MAX_COMMAND_CHARS:
        raise RuntimeError(f'the engine command line would be {size} characters (limit {MAX_COMMAND_CHARS}): too many command breakpoints '
                           f'({len(commands["t"])}) for one call; split the run (fly.py does this by itself)')
    t0 = time.perf_counter()
    with (folder / f'{tag}.engine.log').open('w') as log:
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    wall = time.perf_counter() - t0
    if proc.returncode:
        raise RuntimeError(f'engine failed ({proc.returncode}): ' + (folder / f'{tag}.engine.log').read_text()[-2000:])
    raw = json.loads(out.read_text())
    tr = raw['trace']
    t = np.asarray(tr['time'], float)
    data = {sid: np.asarray(tr['signals'][sid], float) for sid in signal_ids}
    out.unlink()
    return t, data, dict(command=cmd, wall_s=wall, samples=len(t), command_chars=size)


def signals():
    return json.loads((SIM / 'model/signals.json').read_text())


def run_case(params, folder, step=STEP, stop=STOP, start=0.0, overrides=None, commands=None, blocks=False, label=None, save=True, t_far=None):
    """Run one parameter set from `start` to `stop`. Returns (t, {signal name: array}, checks)."""
    folder = Path(folder)
    sig = signals()
    W = dict(params['workspace'])
    W.update(overrides or {})
    commands = params['commands'] if commands is None else commands
    ids = sorted({s['id'] for s in sig.values()})
    receipt = dict(label=label, variant=params.get('variant'), revision=params.get('revision'), placeholder=params.get('placeholder'),
                   model=MODEL.name, model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
                   engine=engine().name, engine_commit=engine_commit(), engine_executable_sha256=hashlib.sha256(engine().read_bytes()).hexdigest(),
                   engine_note='local build with output selection (--signal); integration unchanged',
                   options=dict(start=start, stop=stop, step=step, solver='rk4'), overrides=overrides or {}, effective_workspace=W,
                   commands=commands)
    folder.mkdir(parents=True, exist_ok=True)
    if save:
        (folder / 'request.json').write_text(json.dumps(receipt, indent=1))
    t, by_id, info = call_engine(W, commands, folder, ids, step, stop, start, t_far=t_far)
    receipt.update(engine_wall_s=info['wall_s'], command=info['command'])
    if save:
        (folder / 'request.json').write_text(json.dumps(receipt, indent=1))
    data = {name: by_id[s['id']] for name, s in sig.items()}

    n_expect = int(round((stop - start) / step)) + 1
    checks = dict(samples=len(t), expected_samples=n_expect, time_start=float(t[0]), time_end=float(t[-1]),
                  time_coverage=bool(len(t) == n_expect and abs(t[-1] - stop) < 1e-9 and abs(t[0] - start) < 1e-12),
                  time_monotonic=bool(np.all(np.diff(t) > 0)),
                  aligned=bool(all(len(v) == len(t) for v in data.values())),
                  finite=bool(all(np.isfinite(v).all() for v in data.values())),
                  required_signals=bool(all(s['id'] in by_id for s in sig.values())),
                  quat_norm_max_error=float(np.abs(np.sqrt(data['quat_norm2']) - 1).max()), engine_wall_s=info['wall_s'])
    checks['structural_pass'] = bool(checks['time_coverage'] and checks['time_monotonic'] and checks['aligned'] and checks['finite']
                                     and checks['required_signals'] and checks['quat_norm_max_error'] < 1e-6)
    if save:
        (folder / 'checks.json').write_text(json.dumps(checks, indent=1))
        np.savez_compressed(folder / 'raw.npz', t=t, **data)

    if blocks:
        wiring = json.loads((SIM / 'model/wiring_graph.json').read_text())
        all_ids = [b['id'] for b in wiring['blocks'] if b['type'] != 'Constant']
        per_call = max(1, BUDGET // n_expect)
        got = {}
        for k in range(0, len(all_ids), per_call):
            tb, part, _ = call_engine(W, commands, folder, all_ids[k:k + per_call], step, stop, start, tag=f'blocks{k // per_call}', t_far=t_far)
            assert len(tb) == len(t)
            got.update(part)
        stride = max(1, int(round(1 / (OUT_HZ * step))))
        sid = np.array([int(i.split('/')[1]) for i in got])
        np.savez_compressed(folder / 'block_traces.npz', t=t[::stride].astype(np.float32), sid=sid,
                            values=np.stack([got[i][::stride] for i in got]).astype(np.float32))
        # the block log must reproduce the recorded signals exactly (same integration, different selection)
        worst = max(float(np.abs(got[s['id']] - by_id[s['id']]).max()) for s in sig.values() if s['id'] in got)
        checks['block_log_matches_recorded'] = bool(worst == 0.0)
        checks['block_log_blocks'] = len(got)
        (folder / 'checks.json').write_text(json.dumps(checks, indent=1))
    return t, data, checks


# names of the recorded signals that are the 24 states, in the order of the initial-condition variables
STATE_SIGNALS = ['u', 'v', 'w', 'p', 'q', 'r', 'e0', 'e1', 'e2', 'e3', 'pn', 'pe', 'pd', 'track_unwrapped', 'spool',
                 'stabilator', 'flaperon_left', 'flaperon_right', 'rudder', 'gear',
                 'pitch_integrator', 'throttle_integrator', 'sustained_nz_integrator', 'bank_reference']
STATE_INIT = ['u0', 'v0', 'w0', 'p0', 'q0', 'r0', 'e0_0', 'e1_0', 'e2_0', 'e3_0', 'pn0', 'pe0', 'pd0', 'chi0', 'thr0',
              'de0', 'dfl0', 'dfr0', 'dr0', 'gear0', 'dei0', 'thri0', 'nsi0', 'phir0']


def state_overrides(data, k=-1):
    """Workspace overrides that start a run from sample k of a trace (every state of the model is recorded)."""
    return {init: float(data[name][k]) for name, init in zip(STATE_SIGNALS, STATE_INIT)}


def write_trace(folder, t, data, params, step, extra=None):
    """trace.json at a fixed output step of 1/60 s (every recorded signal, SI units, radians)."""
    sig = signals()
    stride = int(round(1 / (OUT_HZ * step)))
    assert abs(stride * step * OUT_HZ - 1) < 1e-9, 'solver step must divide 1/60 s'
    sel = slice(None, None, stride)
    r = lambda a: [float(f'{x:.7g}') for x in a[sel]]
    trace = dict(variant=params['variant'], name=params['name'], revision=params['revision'], placeholder=params.get('placeholder'),
                 maneuver=params.get('maneuver'), condition=params.get('condition'), dt=1 / OUT_HZ, solver='rk4', solver_step=step,
                 frame='position north/east/down in m from the start point (flat earth); attitude quaternion e0..e3 (scalar first) rotates '
                       'body axes (x forward, y right, z down) into north-east-down; Euler angles phi, theta, psi in rad (3-2-1); '
                       'angles in rad, forces in N, load factors in g. Stored values are SI.',
                 units={n: s['unit'] for n, s in sig.items()}, **(extra or {}), t=r(t), **{n: r(v) for n, v in data.items()})
    (Path(folder) / 'trace.json').write_text(json.dumps(trace, separators=(',', ':')))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('params', help='parameter file written by params.py or run_all.py')
    ap.add_argument('--out', default=None)
    ap.add_argument('--step', type=float, default=STEP)
    ap.add_argument('--stop', type=float, default=STOP)
    ap.add_argument('--blocks', action='store_true')
    a = ap.parse_args()
    params = json.loads(Path(a.params).read_text())
    folder = Path(a.out or SIM / 'runs' / params['revision'] / Path(a.params).stem)
    t, data, checks = run_case(params, folder, a.step, a.stop, blocks=a.blocks, label=params.get('maneuver'))
    write_trace(folder, t, data, params, a.step)
    res = dict(checks=checks)
    (folder / 'result.json').write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    if not checks['structural_pass']:
        sys.exit('structural checks failed; raw results kept')


if __name__ == '__main__':
    main()
