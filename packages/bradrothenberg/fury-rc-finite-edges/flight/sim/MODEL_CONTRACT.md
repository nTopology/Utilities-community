# Fury 6-DOF model: contract

`model/fury_6dof.mdl` is written by `model/build_model.py` (1,203 blocks, 1,777 connections, 14 subsystems, 24 states).
It is a scalar block graph with explicit integrators; nothing in it is tuned per flight. All numbers it needs come
from the workspace (`params.py`), 233 scalars and 18 command vectors (`model/variables.json`). Recorded signals,
their units and block IDs: `model/signals.json` (122 signals).

## Axes and signs

- Body axes: x forward, y to the right wing, z down, origin at the centre of gravity.
- Earth: flat, north / east / down from the start point; height = -down. ISA atmosphere.
- Attitude: quaternion e0..e3 (scalar first), body to north-east-down, with a norm correction term. Euler angles
  phi, theta, psi (3-2-1) are outputs only.
- Angle of attack alpha = atan(w / u); sideslip beta = asin(v / V), positive with the wind from the right.
- Load factor nz positive up (1 in level flight).
- Stabilator and flaperons: positive trailing edge down. Aileron = (left - right) / 2 of the flaperons: positive is left
  trailing edge down, right up, and rolls to the right. Flap = (left + right) / 2. The signs of all eleven control and
  stability derivatives are checked in `lattice.py` (`check()`).
- Model frame of the geometry (only in `params.py`): x aft from the nose, y starboard, z up.

## States (24)

u, v, w; p, q, r; e0..e3; north, east, down; unwrapped track angle; engine spool; stabilator; left and right flaperon;
rudder; landing gear position (0 up, 1 down); pitch integrator; throttle integrator; sustained-load-factor integrator;
bank reference. Every state is recorded, so a run can be stopped and restarted from its trace (`run.state_overrides`).

## Equations

- Rigid body with Ixz, gravity constant, no wind.
- Aerodynamics: CL, CD and Cm against angle of attack from 14-knot tables (hinge form) of one Mach number;
  CD = k CL(alpha)^2 + remainder(alpha). Pitch-rate, stabilator and flap terms linear in an effective deflection that
  loses effectiveness above a break angle. Profile drag of deflected surfaces, gear drag and gear pitching moment scaled
  by the gear position. Lateral coefficients linear in beta, p, r, aileron and rudder, with lift-dependent terms.
- Thrust: installed sea-level static thrust with a lapse in density and Mach number, first-order spool, thrust line
  offset from the centre of gravity.
- Actuators: first order with rate and position limits; gear with its own rate.
- Guidance: track hold with bank from the load factor allowed (structure, lift limit, optionally what thrust
  sustains: `hold_speed`), height hold through a climb-rate command, speed hold through the throttle.
- Pitch law: load-factor command, pole placement on the onboard short-period model, integral action, angle-of-attack
  limiters above and below. Roll: model following of a roll-rate command. Yaw: sideslip and yaw-rate feedback to a
  Dutch-roll target with aileron-rudder interconnect.

## Commands (17 tables over one time vector)

Track, bank, roll rate, their selectors, turn load factor, height, climb-rate limit, load factor and its selector,
Mach, airspeed, throttle and its selector, sideslip, flap, gear. Written by `schedule.py` from rows such as
`{"t": 3, "heading_change_deg": 180, "turn_g": 9}` or `{"t": 2, "gear": "down"}`.

## Numerics

Fixed-step RK4, 1/240 s; traces written at 1/60 s. Checked against the independent Python model at the same step
(agreement to round-off) and at half the sample rate in the web service (position within 0.0004 m over 175 s).

## Limits

- One Mach number of tables per run; valid from stall to about Mach 0.9; no post-stall, no spin.
- No ground effect, ground contact, gear loads, wind or turbulence.
- Flap = both flaperons symmetric; no leading-edge devices, no speed brake.
- Conventional tail only.
- Every aerodynamic, mass and thrust number is an estimate (`../out/aircraft.md`).
