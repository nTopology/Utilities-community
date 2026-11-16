"""Build the 6-DOF flight dynamics model of the Fury model (conventional tail) as an Unlinked (Simulink MDL) graph.

Python writes the graph only. The Unlinked engine integrates it (../run.py, ../fly.py, ../web.py).
The equations are stated in ../MODEL_CONTRACT.md; the same equations are written a second time, independently and in
vector form, in ../verify/ref6dof.py.

Everything that differs between weights, flight conditions and commands is a workspace variable (../params.py; command
time tables from ../schedule.py).

Ported from an earlier flight study by the same author: rigid body,
quaternion attitude, ISA, coefficient tables in hinge form, thrust lapse, guidance and the three control laws are the
same equations. What is different here:
  - controls: one all-moving horizontal tail (stabilator, both panels together), a left and a right flaperon (flap
    together, aileron against each other) and one rudder,
  - landing gear: a travel state (0 up, 1 down) driven by a command table; its drag and pitching moment,
  - flap: a command table that moves both flaperons down; the aileron command rides on it,
  - separate large-deflection effectiveness curves for the all-moving tail and for the plain flaps.

Writes fury_6dof.mdl, signals.json, wiring_graph.json, variables.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from graph import Graph  # noqa: E402

NAME = 'fury_6dof'
N_KNOT = 14                      # angle-of-attack knots of the three coefficient tables
STEP = 1 / 240                   # solver step written into the file (the run passes it explicitly)

# command time tables: name -> (workspace vector, unit, what it is)
SCHEDULES = dict(
    chi=('sch_chi', 'rad', 'track angle target (unwrapped)'),
    phi=('sch_phi', 'rad', 'bank angle target (bank mode)'),
    p=('sch_p', 'rad/s', 'roll rate command (roll stick)'),
    sel_bank=('sch_sel_bank', '-', '1: lateral axis follows the bank target'),
    sel_rate=('sch_sel_rate', '-', '1: lateral axis follows the roll rate command'),
    n_turn=('sch_n_turn', 'g', 'load factor allowed in a turn to a track target'),
    h=('sch_h', 'm', 'height target'),
    vs_max=('sch_vs_max', 'm/s', 'climb and descent rate allowed by the height hold'),
    nz=('sch_nz', 'g', 'load factor command (pitch stick)'),
    sel_nz=('sch_sel_nz', '-', '1: pitch axis follows the load factor command'),
    mach=('sch_mach', '-', 'Mach number target'),
    tas=('sch_tas', 'm/s', 'true airspeed target (added to Mach target times speed of sound)'),
    thr=('sch_thr', '-', 'throttle command (throttle lever)'),
    sel_thr=('sch_sel_thr', '-', '1: throttle follows the throttle command'),
    beta=('sch_beta', 'rad', 'sideslip target (pedal)'),
    flap=('sch_flap', 'rad', 'flap command (both flaperons trailing edge down)'),
    gear=('sch_gear', '-', 'landing gear command (0 up, 1 down)'),
)
SCHEDULE_TIME = 'sch_t'

# parts of the aircraft a block or subsystem belongs to
PART_CG = 'cg'
PART_MRP = 'wing_reference_point'
PART_ENGINE = 'engine'
PART_AVIONICS = 'avionics_bay'
PART_AIRDATA = 'air_data_probe'
PART_FCC = 'flight_control_computer'
PART_AIRFRAME = 'airframe'
FLAPERONS = [('fl', 'left flaperon', 'flaperon_left', 1.0), ('fr', 'right flaperon', 'flaperon_right', -1.0)]


def build():
    g = Graph(NAME)
    c = g.c

    # =====================================================================================
    # States. Created first so every subsystem can read them; derivatives are wired at the end.
    # =====================================================================================
    g.subsystem('Translation', 'Body-axis force equations: du/dt, dv/dt, dw/dt from force per mass and the rotating frame.', PART_CG)
    u = g.state('u body velocity forward', 'u0', 'm/s', PART_CG)
    v = g.state('v body velocity right', 'v0', 'm/s', PART_CG)
    w = g.state('w body velocity down', 'w0', 'm/s', PART_CG)
    g.subsystem('Rotation', 'Body-axis moment equations with the full inertia tensor (Ixx, Iyy, Izz, Ixz).', PART_CG)
    p = g.state('p roll rate', 'p0', 'rad/s', PART_CG)
    q = g.state('q pitch rate', 'q0', 'rad/s', PART_CG)
    r = g.state('r yaw rate', 'r0', 'rad/s', PART_CG)
    g.subsystem('Attitude and position', 'Attitude quaternion (body to north-east-down), direction cosines, Euler angles, '
                'flat-earth position and the unwrapped track angle.', PART_AIRFRAME)
    e0 = g.state('quaternion e0', 'e0_0', '-', PART_AIRFRAME)
    e1 = g.state('quaternion e1', 'e1_0', '-', PART_AIRFRAME)
    e2 = g.state('quaternion e2', 'e2_0', '-', PART_AIRFRAME)
    e3 = g.state('quaternion e3', 'e3_0', '-', PART_AIRFRAME)
    pn = g.state('position north', 'pn0', 'm', PART_AIRFRAME)
    pe = g.state('position east', 'pe0', 'm', PART_AIRFRAME)
    pd = g.state('position down', 'pd0', 'm', PART_AIRFRAME)
    chi_u = g.state('track angle unwrapped', 'chi0', 'rad', PART_AIRFRAME)
    g.subsystem('Propulsion', 'Engine: thrust available from ISA height and Mach number, first-order spool lag, thrust along body x '
                'through the engine station.', PART_ENGINE)
    thr = g.state('spool state (thrust fraction)', 'thr0', '-', PART_ENGINE)
    g.subsystem('Mixer and actuators', 'Pitch command to the stabilator, flap and aileron commands to the two flaperons, position limits, '
                'rate-limited first-order actuators for the stabilator, the flaperons and the rudder; landing gear travel.', 'controls')
    de = g.state('stabilator deflection (both panels)', 'de0', 'rad', 'stabilator')
    surf = {k: g.state(f'{label} deflection', f'd{k}0', 'rad', part) for k, label, part, _ in FLAPERONS}
    dr = g.state('rudder deflection', 'dr0', 'rad', 'rudder')
    gear = g.state('landing gear travel (0 up, 1 down)', 'gear0', '-', 'landing_gear')
    g.subsystem('Pitch law', 'Load-factor command law with angle-of-attack limiter: gains from the short-period derivatives and '
                'dynamic pressure, integral action as a stabilator trim state.', PART_FCC)
    de_i = g.state('pitch integrator (stabilator trim)', 'dei0', 'rad', PART_FCC)
    g.subsystem('Guidance', 'Commands from the time tables: track, bank or roll rate; height or load factor; speed or throttle. Bank command '
                'for a level turn at the available load factor, height hold through load factor, speed hold, throttle.', PART_FCC)
    thr_i = g.state('throttle integrator', 'thri0', '-', PART_FCC)
    ns_i = g.state('sustained load factor integrator', 'nsi0', 'g', PART_FCC)
    g.subsystem('Roll and yaw laws', 'Bank-angle hold through a roll-rate command; roll stick as a rate command with attitude hold (a bank '
                'reference that the stick moves); sideslip command and turn coordination with the rudder; aileron-to-rudder '
                'interconnect. Gains from the roll and yaw derivatives and dynamic pressure.', PART_FCC)
    phi_ref = g.state('bank reference of the roll stick', 'phir0', 'rad', PART_FCC)

    # =====================================================================================
    g.subsystem('Commands', 'Command inputs as time tables (linear interpolation of workspace vectors over one time vector) and an optional '
                'track step. Written by schedule.py from a schedule; constant for a trim run.', PART_FCC)
    sch = {k: g.schedule(f'table: {what}', SCHEDULE_TIME, var, unit, PART_FCC) for k, (var, unit, what) in SCHEDULES.items()}
    chi_step = g.step('t_turn', 0, 'chi_turn', 'track step')
    g.nodes[chi_step.i - 1]['unit'] = 'rad'
    chi_cmd = (sch['chi'] + chi_step).n('track angle command', 'rad')
    sel_lat = g.max(sch['sel_bank'], sch['sel_rate']).n('lateral axis flown by bank or roll rate command', '-')

    # =====================================================================================
    g.subsystem('Attitude and position', '')
    e00, e11, e22, e33 = e0 * e0, e1 * e1, e2 * e2, e3 * e3
    c11 = (e00 + e11 - e22 - e33).n('C11', '-')
    c12 = (2.0 * (e1 * e2 - e0 * e3)).n('C12', '-')
    c13 = (2.0 * (e1 * e3 + e0 * e2)).n('C13', '-')
    c21 = (2.0 * (e1 * e2 + e0 * e3)).n('C21', '-')
    c22 = (e00 - e11 + e22 - e33).n('C22', '-')
    c23 = (2.0 * (e2 * e3 - e0 * e1)).n('C23', '-')
    c31 = (2.0 * (e1 * e3 - e0 * e2)).n('C31 (-sin pitch)', '-')
    c32 = (2.0 * (e2 * e3 + e0 * e1)).n('C32 (sin bank cos pitch)', '-')
    c33 = (e00 - e11 - e22 + e33).n('C33 (cos bank cos pitch)', '-')
    vn = (c11 * u + c12 * v + c13 * w).n('velocity north', 'm/s')
    ve = (c21 * u + c22 * v + c23 * w).n('velocity east', 'm/s')
    vd = (c31 * u + c32 * v + c33 * w).n('velocity down', 'm/s')
    phi = g.atan2(c32, c33).n('bank angle', 'rad')
    theta = g.asin(g.clip(-c31, -1, 1)).n('pitch angle', 'rad')
    psi = g.atan2(c21, c11).n('heading', 'rad')
    height = (-pd).n('height', 'm')
    climb = (-vd).n('climb rate', 'm/s')
    qnorm2 = (e00 + e11 + e22 + e33).n('quaternion norm squared', '-')
    qfix = (c('quat_lambda') * (1.0 - qnorm2)).n('norm correction', '1/s')

    # =====================================================================================
    g.subsystem('Air data', 'ISA atmosphere from height; true airspeed, angle of attack, sideslip, dynamic pressure and Mach number '
                'from the body velocity.', PART_AIRDATA)
    h_isa = g.clip(height, -500, 11000).n('height in troposphere', 'm')
    t_air = (288.15 - 0.0065 * h_isa).n('air temperature', 'K')
    theta_isa = (t_air / 288.15).n('temperature ratio', '-')
    delta_isa = g.pow(theta_isa, 5.255877).n('pressure ratio', '-')
    p_air = (101325.0 * delta_isa).n('static pressure', 'Pa')
    rho = (p_air / (287.05287 * t_air)).n('air density', 'kg/m3')
    a_snd = g.sqrt(401.874018 * t_air).n('speed of sound', 'm/s')
    v2 = (u * u + v * v + w * w).n('airspeed squared', 'm2/s2')
    vt = g.max(g.sqrt(v2), 1.0).n('true airspeed', 'm/s')
    alpha = g.atan2(w, u).n('angle of attack', 'rad')
    beta = g.asin(g.clip(v / vt, -1, 1)).n('sideslip angle', 'rad')
    qbar = (0.5 * rho * v2).n('dynamic pressure', 'Pa')
    mach = (vt / a_snd).n('Mach number', '-')

    # =====================================================================================
    g.subsystem('Aerodynamics', 'Coefficients about the moment reference point: lift (with a maximum and a stall break), drag and pitching '
                'moment tables over angle of attack; stabilator, flaperon and rudder derivatives; landing gear increments; sideslip '
                'and damping derivatives; forces in body axes.', PART_MRP)

    def effective(d, kind, label):
        # large-deflection effectiveness: slope <kind>_k1 up to <kind>_break, reduced by <kind>_k2 beyond it
        over = g.max(d - c(f'{kind}_break'), 0.0) - g.max(-d - c(f'{kind}_break'), 0.0)
        return (c(f'{kind}_k1') * d - c(f'{kind}_k2') * over).n(label, 'rad')

    de_e = effective(de, 'stab', 'stabilator effective deflection')
    eff = {k: effective(surf[k], 'flap', f'{label} effective deflection') for k, label, _, _ in FLAPERONS}
    df_e = (0.5 * (eff['fl'] + eff['fr'])).n('flaperons: symmetric part (flap, effective)', 'rad')
    da_e = (0.5 * (eff['fl'] - eff['fr'])).n('flaperons: differential part (aileron, effective)', 'rad')
    sin2 = lambda x: g.sin(x) * g.sin(x)
    prof_s = sin2(de).n('stabilator: sin2 of the deflection', '-')
    prof_f = (0.5 * (sin2(surf['fl']) + sin2(surf['fr']))).n('flaperons: mean sin2 of the deflection', '-')
    prof_r = sin2(dr).n('rudder: sin2 of the deflection', '-')
    a_t = g.clip(alpha, 'ak_0', f'ak_{N_KNOT - 1}').n('table angle of attack', 'rad')
    hinges = [g.max(a_t - c(f'ak_{i}'), 0.0).n(f'hinge {i}', 'rad') for i in range(1, N_KNOT - 1)]
    da0 = a_t - c('ak_0')

    def table(prefix, label):
        y = c(f'{prefix}_0') + c(f'{prefix}_m0') * da0
        for i, hgn in enumerate(hinges, 1):
            y = y + c(f'{prefix}_d{i}') * hgn
        return y.n(label, '-')

    cl_t = table('cl', 'CL table')
    cd_r = table('cd', 'CD table: remainder to the parabolic polar')
    cm_t = table('cm', 'Cm table')
    two_v = 2.0 * vt
    ph = (p * c('b_ref') / two_v).n('p b/2V', '-')
    qh = (q * c('c_ref') / two_v).n('q c/2V', '-')
    rh = (r * c('b_ref') / two_v).n('r b/2V', '-')
    cl_w = (cl_t + c('cl_q') * qh).n('CL at zero deflection (angle of attack and pitch rate)', '-')
    cl = (cl_w + c('cl_de') * de_e + c('cl_df') * df_e).n('CL', '-')
    cl_t2 = (cl_t * cl_t).n('CL table squared', '-')
    cd_t = (cd_r + c('cd_pol_k') * cl_t2).n('CD at zero deflection (polar at the lift of the angle-of-attack table)', '-')
    # drag of the deflected surfaces: induced (cross term with the wing lift, quadratic term) and profile drag with sin2 of the deflection
    cd_ind = (c('cd_de1') * cl_t * de_e + c('cd_de3') * de_e * de_e + c('cd_df1') * cl_t * df_e + c('cd_df3') * df_e * df_e).n('CD induced by stabilator and flap', '-')
    cd_prof = (c('cd_de2') * prof_s + c('cd_df2') * prof_f + c('cd_dr2') * prof_r).n('CD profile of deflected surfaces', '-')
    cd_lg = (c('cd_gear') * gear).n('CD landing gear', '-', 'landing_gear')
    cd = (cd_t + cd_ind + cd_prof + cd_lg).n('CD', '-')
    cm = (cm_t + c('cm_q') * qh + c('cm_de') * de_e + c('cm_df') * df_e + c('cm_gear') * gear).n('Cm', '-')
    cy = (c('cy_b') * beta + c('cy_p') * ph + c('cy_r') * rh + c('cy_da') * da_e + c('cy_dr') * dr).n('CY', '-')
    cll = ((c('cll_b0') + c('cll_b1') * cl_t) * beta + c('cll_p') * ph + (c('cll_r0') + c('cll_r1') * cl_t) * rh
           + c('cll_da') * da_e + c('cll_dr') * dr).n('Cl roll', '-')
    cn = ((c('cn_b0') + c('cn_b1') * cl_t2) * beta + (c('cn_p0') + c('cn_p1') * cl_t) * ph + (c('cn_r0') + c('cn_r1') * cl_t2) * rh
          + c('cn_da') * da_e + c('cn_dr') * dr).n('Cn yaw', '-')
    qs = (qbar * c('s_ref')).n('q S', 'N')
    sa, ca = g.sin(alpha).n('sin alpha'), g.cos(alpha).n('cos alpha')
    lift = (qs * cl).n('lift', 'N', PART_MRP)
    drag = (qs * cd).n('drag', 'N', PART_MRP)
    xa = (lift * sa - drag * ca).n('aero force X', 'N', PART_MRP)
    ya = (qs * cy).n('aero force Y', 'N', PART_MRP)
    za = (-(drag * sa) - lift * ca).n('aero force Z', 'N', PART_MRP)
    l_ref = (qs * c('b_ref') * cll).n('rolling moment at reference point', 'N m', PART_MRP)
    m_ref = (qs * c('c_ref') * cm).n('pitching moment at reference point', 'N m', PART_MRP)
    n_ref = (qs * c('b_ref') * cn).n('yawing moment at reference point', 'N m', PART_MRP)

    # =====================================================================================
    g.subsystem('Propulsion', '')
    m2 = mach * mach
    ram = (1.0 + 0.2 * m2).n('1 + 0.2 M2', '-')
    theta0 = (theta_isa * ram).n('total temperature ratio', '-')
    delta0 = (delta_isa * g.pow(ram, 3.5)).n('total pressure ratio', '-')
    sigma = (rho / 1.225).n('density ratio', '-')
    lapse_m = (delta0 * (1.0 - c('eng_k_m') * g.sqrt(mach) - c('eng_k_theta') * g.max(theta0 - c('eng_tr'), 0.0)
                         / (c('eng_c_t') * theta0 + c('eng_c_0') + c('eng_c_m') * mach))).n('thrust lapse, Mattingly form', '-')
    lapse_d = (g.pow(sigma, 'eng_n_sig') * (1.0 + c('eng_a1') * mach + c('eng_a2') * m2)).n('thrust lapse, density form', '-')
    lapse = (c('eng_w_matt') * lapse_m + c('eng_w_dens') * lapse_d).n('thrust lapse', '-')
    t_avail = (c('t_sls') * lapse).n('thrust available', 'N', PART_ENGINE)
    thrust = (thr * t_avail).n('thrust', 'N', PART_ENGINE)

    # =====================================================================================
    g.subsystem('Gravity', 'Weight resolved into body axes with the third row of the direction cosine matrix.', PART_CG)
    wgt = c('mass') * c('g0')
    gx = (wgt * c31).n('weight X', 'N', PART_CG)
    gy = (wgt * c32).n('weight Y', 'N', PART_CG)
    gz = (wgt * c33).n('weight Z', 'N', PART_CG)

    # =====================================================================================
    g.subsystem('Forces and moments', 'Sum of aerodynamic force, thrust and weight at the centre of gravity; aerodynamic moments moved '
                'from the reference point to the centre of gravity; thrust-line moment; load factors.', PART_CG)
    fx = (xa + thrust + gx).n('force X', 'N', PART_CG)
    fy = (ya + gy).n('force Y', 'N', PART_CG)
    fz = (za + gz).n('force Z', 'N', PART_CG)
    l_cg = (l_ref - c('mrp_z') * ya).n('rolling moment L', 'N m', PART_CG)
    m_cg = (m_ref + c('mrp_z') * xa - c('mrp_x') * za + c('eng_z') * thrust).n('pitching moment M', 'N m', PART_CG)
    n_cg = (n_ref + c('mrp_x') * ya).n('yawing moment N', 'N m', PART_CG)
    nz = (-za / wgt).n('load factor nz', 'g', PART_CG)
    ny = (ya / wgt).n('load factor ny', 'g', PART_CG)
    nx = ((xa + thrust) / wgt).n('load factor nx', 'g', PART_CG)

    # =====================================================================================
    g.subsystem('Attitude and position', '')
    acc_n = ((c11 * fx + c12 * fy + c13 * fz) / c('mass')).n('acceleration north', 'm/s2')
    acc_e = ((c21 * fx + c22 * fy + c23 * fz) / c('mass')).n('acceleration east', 'm/s2')
    chi_dot = ((vn * acc_e - ve * acc_n) / g.max(vn * vn + ve * ve, 1.0)).n('track angle rate', 'rad/s')

    g.subsystem('Translation', '')
    u_dot = (r * v - q * w + fx / c('mass')).n('du/dt', 'm/s2')
    v_dot = (p * w - r * u + fy / c('mass')).n('dv/dt', 'm/s2')
    w_dot = (q * u - p * v + fz / c('mass')).n('dw/dt', 'm/s2')

    g.subsystem('Rotation', '')
    hx = (c('ixx') * p - c('ixz') * r).n('angular momentum x', 'kg m2/s')
    hy = (c('iyy') * q).n('angular momentum y', 'kg m2/s')
    hz = (c('izz') * r - c('ixz') * p).n('angular momentum z', 'kg m2/s')
    tx = (l_cg - (q * hz - r * hy)).n('torque less gyroscopic x', 'N m')
    ty = (m_cg - (r * hx - p * hz)).n('torque less gyroscopic y', 'N m')
    tz = (n_cg - (p * hy - q * hx)).n('torque less gyroscopic z', 'N m')
    gam = c('ixx') * c('izz') - c('ixz') * c('ixz')
    p_dot = ((c('izz') * tx + c('ixz') * tz) / gam).n('dp/dt', 'rad/s2')
    q_dot = (ty / c('iyy')).n('dq/dt', 'rad/s2')
    r_dot = ((c('ixz') * tx + c('ixx') * tz) / gam).n('dr/dt', 'rad/s2')

    # =====================================================================================
    g.subsystem('Sensors', 'Rate gyros, accelerometers and attitude reference in the avionics bay; air data from the probe. '
                'Ideal taps: no lag, no noise, sensed at the centre of gravity.', PART_AVIONICS)

    def tap(x, label, unit, part=PART_AVIONICS):
        return g.op('Gain', [x], Gain='1').n(label, unit, part)

    s_p, s_q, s_r = tap(p, 'gyro roll rate', 'rad/s'), tap(q, 'gyro pitch rate', 'rad/s'), tap(r, 'gyro yaw rate', 'rad/s')
    s_nz = tap(nz, 'accelerometer nz', 'g')
    s_phi = tap(phi, 'attitude bank', 'rad')
    s_c32, s_c33 = tap(c32, 'attitude sin bank cos pitch', '-'), tap(c33, 'attitude cos bank cos pitch', '-')
    s_chi = tap(chi_u, 'track angle reference', 'rad')
    s_h, s_hd = tap(height, 'height sensed', 'm'), tap(climb, 'climb rate sensed', 'm/s')
    s_alpha = tap(alpha, 'probe angle of attack', 'rad', PART_AIRDATA)
    s_beta = tap(beta, 'probe sideslip', 'rad', PART_AIRDATA)
    s_v = tap(vt, 'probe true airspeed', 'm/s', PART_AIRDATA)
    s_qbar = tap(qbar, 'probe dynamic pressure', 'Pa', PART_AIRDATA)
    s_a = tap(a_snd, 'probe speed of sound', 'm/s', PART_AIRDATA)
    s_dr = tap(dr, 'rudder position sensed', 'rad', 'rudder')

    # =====================================================================================
    g.subsystem('Guidance', '')
    wg = c('mass') * c('g0')
    e_psi = ((1.0 - sel_lat) * (chi_cmd - s_chi)).n('track angle error', 'rad')
    qs_g = s_qbar * c('s_ref')
    n_alpha_lim = (c('k_av') * qs_g * c('fcs_cl_lim') / wg).n('load factor at the angle-of-attack limit', 'g')
    n_cap = g.min(g.min(n_alpha_lim, c('k_bank') * c('nz_lim')), sch['n_turn']).n('load factor limit other than thrust', 'g')
    # load factor that full thrust sustains: onboard drag polar (feedforward) trimmed by a PI law on the speed error (active in the turn)
    cd_ex = g.max(t_avail / qs_g - c('fcs_cd0'), 0.0).n('full-thrust coefficient above zero-lift drag', '-')
    n_ff = (qs_g * g.sqrt(cd_ex / c('fcs_cdk')) / wg).n('load factor full thrust sustains (onboard polar)', 'g')
    v_cmd = (sch['mach'] * s_a + sch['tas']).n('airspeed command', 'm/s')
    v_err = (s_v - v_cmd).n('airspeed above command', 'm/s')
    turn_flag = g.clip((g.abs(e_psi) - c('e_thr_on')) / c('e_thr_band'), 0, 1).n('turn flag', '-')
    # hold_speed = 1: the turn is cut back to what thrust sustains at the commanded speed; 0: the turn is flown at the load factor
    # asked for and the speed is let go (a hard turn that bleeds speed)
    n_spd_unsat = (n_ff + ns_i + c('k_ns_p') * v_err).n('speed-hold load factor before limit', 'g')
    n_spd_lim = g.clip_dyn(n_spd_unsat, c('n_av_min'), 2.0 * c('nz_lim')).n('load factor that holds the speed', 'g')
    n_spd = (c('hold_speed') * n_spd_lim + (1.0 - c('hold_speed')) * 2.0 * c('nz_lim')).n('load factor allowed by the speed hold', 'g')
    n_av = g.clip_dyn(g.min(n_cap, n_spd), c('n_av_min'), c('nz_lim')).n('available load factor', 'g')
    thrust_flag = g.clip((n_cap - n_spd) / c('dn_thr') + 1.0, 0, 1).n('thrust flag (thrust is what limits the turn)', '-')
    # height hold: climb rate command from the height error, limited; vertical load factor demand from the climb rate error
    hd_cmd = g.clip_dyn(c('k_h') * (sch['h'] - s_h) / c('k_hd'), -sch['vs_max'], sch['vs_max']).n('climb rate command', 'm/s')
    nv = (c('nv0') + g.clip(c('k_hd') * (hd_cmd - s_hd), '-nv_band', 'nv_band')).n('vertical load factor demand', 'g')
    n_bank = g.max(s_nz, g.min(s_nz + c('dn_lead'), n_av)).n('load factor the bank is set for', 'g')
    n_bank_f = g.max(n_bank, c('n_av_min'))
    nvb = g.min(c('nv_band'), c('k_nvb') * (n_bank_f - 1.0)).n('vertical load factor band of the bank', 'g')
    nv_b = (c('nv0') + g.clip_dyn(c('k_hd') * (hd_cmd - s_hd), -nvb, nvb)).n('vertical load factor demand of the bank', 'g')
    phi_turn = g.acos(g.clip(nv_b / n_bank_f, 0, 1)).n('bank limit', 'rad')
    qsb = s_qbar * c('s_ref') * c('b_ref')
    b2v = (c('b_ref') / (2.0 * s_v)).n('b / 2V', 's')
    cl_on = g.clip_dyn(s_nz * c('mass') * c('g0') / (s_qbar * c('s_ref')), 0.0, c('fcs_cl_cap')).n('onboard lift coefficient', '-')
    cl_pl = g.clip_dyn(n_bank_f * c('mass') * c('g0') / (s_qbar * c('s_ref')), 0.0, c('fcs_cl_cap')).n('onboard lift coefficient the bank is set for', '-')
    cl_on2 = cl_on * cl_on
    l_p = (qsb * b2v * c('fcs_cll_p') / c('ixx')).n('L p (roll damping)', '1/s')
    l_r = (qsb * b2v * (c('fcs_cll_r0') + c('fcs_cll_r1') * cl_on) / c('ixx')).n('L r (roll due to yaw rate)', '1/s')
    l_da = (qsb * c('fcs_cll_da') / c('ixx')).n('L delta (aileron power)', '1/s2')
    l_dr = (qsb * c('fcs_cll_dr') / c('ixx')).n('L rudder', '1/s2')
    l_b = (qsb * (c('fcs_cll_b0') + c('fcs_cll_b1') * cl_on) / c('ixx')).n('L beta (roll due to sideslip)', '1/s2')
    n_b = (qsb * (c('fcs_cn_b0') + c('fcs_cn_b1') * cl_on2) / c('izz')).n('N beta', '1/s2')
    n_r = (qsb * b2v * (c('fcs_cn_r0') + c('fcs_cn_r1') * cl_on2) / c('izz')).n('N r (yaw damping)', '1/s')
    n_p = (qsb * b2v * (c('fcs_cn_p0') + c('fcs_cn_p1') * cl_on) / c('izz')).n('N p (yaw due to roll rate)', '1/s')
    n_dr = (qsb * c('fcs_cn_dr') / c('izz')).n('N rudder (rudder power)', '1/s2')
    n_da = (qsb * c('fcs_cn_da') / c('izz')).n('N aileron (yaw due to aileron)', '1/s2')
    # roll rate limit from the rudder: the share k_pr of the rudder power has to cover the yawing moment of a steady roll rate
    # and the yaw acceleration that keeps the roll about the flight path at angle of attack
    n_p_pl = (qsb * b2v * (c('fcs_cn_p0') + c('fcs_cn_p1') * cl_pl) / c('izz')).n('N p at the lift the bank is set for', '1/s')
    n_p_net = (n_p_pl - n_da * l_p / l_da).n('yaw acceleration per roll rate with its aileron', '1/s')
    n_p_kin = (g.tan(g.max(s_alpha, 0.0)) / c('tau_roll')).n('yaw acceleration per roll rate of a roll about the flight path', '1/s')
    p_lim = g.clip(c('k_pr') * g.abs(n_dr) * c('dr_max') / g.max(g.abs(n_p_net) + n_p_kin, 1e-4), 'p_min', 'p_max').n('roll rate limit', 'rad/s')
    x_ro = (c('k_ro') * g.abs(e_psi) * s_v * p_lim / c('g0')).n('roll-out measure of the track error', '-')
    phi_ro = g.acos(g.clip(g.pow(c(math.e), -x_ro), 0, 1)).n('largest bank that can still be rolled out', 'rad')
    phi_want = g.clip_dyn(c('k_psi') * e_psi, -phi_ro, phi_ro).n('bank wanted by the track error', 'rad')
    phi_hdg = g.clip_dyn(phi_want, -phi_turn, phi_turn).n('bank command of the track hold', 'rad')
    phi_cmd = ((1.0 - sch['sel_bank']) * phi_hdg + sch['sel_bank'] * sch['phi']).n('bank command', 'rad')
    pull_flag = ((1.0 - sel_lat) * g.clip((g.abs(phi_want) - phi_turn) / c('phi_band') + 1.0, 0, 1)
                 * g.clip(g.abs(phi_want) / c('phi_band'), 0, 1)).n('pull flag (bank command on its limit)', '-')
    nz_level = (nv / g.max(s_c33, c('c33_min'))).n('load factor that holds the height at this bank', 'g')
    nz_pull = g.min(n_av, (nv + g.min(c('dnv_pull'), nvb)) / g.max(s_c33, c('c33_min'))).n('load factor of the pull (not ahead of the bank)', 'g')
    nz_auto = (pull_flag * nz_pull + (1.0 - pull_flag) * nz_level).n('load factor command of the height hold and turn', 'g')
    nz_cmd = g.clip((1.0 - sch['sel_nz']) * nz_auto + sch['sel_nz'] * sch['nz'], 'nz_min', 'nz_lim').n('load factor command', 'g')
    # throttle: speed hold; feedforward for the drag of the load factor; or the throttle command
    thr_p = (c('mass') * (v_cmd - s_v) / (c('tau_v') * t_avail)).n('throttle proportional part', '-')
    pull_prog = g.clip((s_nz - 1.0) / (c('k_tp') * (n_av - 1.0)), 0, 1).n('share of the available load factor reached', '-')
    n_want = g.max(s_nz, turn_flag * pull_flag * pull_prog * n_cap).n('load factor the throttle is set for', 'g')
    thr_ff = (c('fcs_cdk') * wg * wg * (g.max(n_want * n_want, 1.0) - 1.0) / (qs_g * t_avail)).n('throttle for the drag of the load factor', '-')
    thr_unsat = (thr_i + thr_p + thr_ff).n('speed-hold throttle', '-')
    thr_sat = g.clip(thr_unsat, 'thr_idle', 1).n('speed-hold throttle inside its range', '-')
    thr_auto = thr_sat
    ns_i_dot = (turn_flag * (c('k_ns_i') * v_err + c('k_rel') * (1.0 - thr_auto) + (n_spd_lim - n_spd_unsat) / c('tau_aw'))
                - (1.0 - turn_flag) * ns_i / c('tau_ns_reset')).n('d(sustained load factor integrator)/dt', 'g/s')
    thr_cmd = g.clip((1.0 - sch['sel_thr']) * thr_auto + sch['sel_thr'] * sch['thr'], 'thr_idle', 1).n('throttle command', '-', PART_ENGINE)
    thr_pi = thr_i + thr_p
    thr_i_dot = (thr_p / c('tau_vi') + (g.clip(thr_pi, 'thr_idle', 1) - thr_pi) / c('tau_aw')).n('d(throttle integrator)/dt', '1/s')

    # =====================================================================================
    g.subsystem('Pitch law', '')
    qs_p = s_qbar * c('s_ref')
    z_al = (qs_p * c('fcs_cla') / (c('mass') * s_v)).n('Z alpha (lift per speed)', '1/s')
    m_al = (qs_p * c('c_ref') * c('fcs_cma') / c('iyy')).n('M alpha', '1/s2')
    m_q = (qs_p * c('c_ref') * c('c_ref') * c('fcs_cm_q') / (2.0 * s_v * c('iyy'))).n('M q', '1/s')
    m_de = (qs_p * c('c_ref') * c('fcs_cm_de') / c('iyy')).n('M delta (stabilator power)', '1/s2')
    n_al = (qs_p * c('fcs_cla') / (c('mass') * c('g0'))).n('N alpha (g per rad)', 'g/rad')
    a2 = c('p_int') + 2.0 * c('z_sp') * c('w_sp')
    a1 = c('w_sp') * c('w_sp') + 2.0 * c('z_sp') * c('w_sp') * c('p_int')
    a0 = c('p_int') * c('w_sp') * c('w_sp')
    mq_cl = z_al - a2
    k_q = (m_q - mq_cl).n('gain on pitch rate', '1/s')
    k_p = ((a1 + z_al * mq_cl) / n_al).n('gain on the selected error', '1/(g s2)')
    k_i = (a0 / n_al).n('integral gain', '1/(g s3)')
    e_nz = (nz_cmd - s_nz).n('load factor error', 'g')
    e_al = (n_al * (c('alpha_lim') - s_alpha)).n('angle-of-attack margin as load factor', 'g')
    e_al_lo = (n_al * (c('alpha_min') - s_alpha)).n('margin to the lower angle-of-attack limit as load factor', 'g')
    e_sel = g.max(g.min(e_nz, e_al), e_al_lo).n('selected error (limiters)', 'g')
    q_ref = (c('g0') * (nz_cmd - s_c33) / s_v).n('pitch rate for the commanded load factor', 'rad/s')
    de_unsat = (de_i - (m_al * s_alpha + k_q * (s_q - q_ref) - k_p * e_sel) / m_de).n('stabilator command before limit', 'rad')
    de_cmd = g.clip(de_unsat, 'de_min', 'de_max').n('stabilator command (linear demand)', 'rad')
    de_i_dot = (k_i * e_sel / m_de + (de_cmd - de_unsat) / c('tau_aw')).n('d(pitch integrator)/dt', 'rad/s')

    # =====================================================================================
    g.subsystem('Roll and yaw laws', '')
    p_hold = g.clip_dyn(c('k_phi') * (phi_cmd - s_phi), -p_lim, p_lim).n('roll rate command of the bank hold', 'rad/s')
    d_ref = phi_ref - s_phi
    e_ref = g.atan2(g.sin(d_ref), g.cos(d_ref)).n('bank reference minus bank (wrapped)', 'rad')
    p_stick_in = g.clip_dyn(sch['p'], -p_lim, p_lim).n('roll stick inside the roll rate limit', 'rad/s')
    p_stick = (g.clip_dyn(c('k_phi') * e_ref, -p_lim, p_lim) + p_stick_in).n('roll rate command of the roll stick', 'rad/s')
    p_cmd = ((1.0 - sch['sel_rate']) * p_hold + sch['sel_rate'] * p_stick).n('roll rate command', 'rad/s')
    phi_ref_dot = (sch['sel_rate'] * p_stick_in - (1.0 - sch['sel_rate']) * e_ref / c('tau_ref')).n('d(bank reference)/dt', 'rad/s')
    da_unsat = (((p_cmd - s_p) / c('tau_roll') - l_p * s_p - l_r * s_r - l_dr * s_dr - l_b * s_beta) / l_da).n('aileron command before limit', 'rad')
    da_cmd = g.clip(da_unsat, '-da_max', 'da_max').n('aileron command (linear demand)', 'rad')
    k_b = g.clip_dyn(c('w_dr') * c('w_dr') - n_b, 0.0, c('kb_max') * g.abs(n_dr)).n('gain on sideslip', '1/s2')
    w_yaw = g.sqrt(g.max(k_b + n_b, 0.0)).n('sideslip frequency reached', 'rad/s')
    k_r = g.clip_dyn(2.0 * c('z_dr') * w_yaw + n_r, 0.0, c('kr_max') * g.abs(n_dr)).n('gain on yaw rate', '1/s')
    r_ref = (s_p * g.tan(s_alpha) + c('g0') * s_c32 / s_v).n('yaw rate for a coordinated turn', 'rad/s')
    dr_unsat = ((k_b * s_beta - (k_b + n_b) * sch['beta'] - k_r * (s_r - r_ref) - n_da * da_cmd - n_p * s_p) / n_dr).n('rudder command before limit', 'rad')
    dr_cmd = g.clip(dr_unsat, '-dr_max', 'dr_max').n('rudder command', 'rad', 'rudder')

    # =====================================================================================
    g.subsystem('Mixer and actuators', '')

    def inverse(raw, kind):
        # the laws work with a linear surface (effectiveness <kind>_k1); beyond the break the surface is less effective,
        # so the mixer asks for more deflection there: the inverse of the effectiveness curve of the aerodynamics
        over = g.max(raw - c(f'{kind}_break'), 0.0) - g.max(-raw - c(f'{kind}_break'), 0.0)
        return raw + c(f'{kind}_inv') * over

    stab_cmd = g.clip(inverse(de_cmd, 'stab'), 'stab_min', 'stab_max').n('stabilator command', 'rad', 'stabilator')
    de_dot = g.clip((stab_cmd - de) / c('act_tau'), '-surf_rate', 'surf_rate').n('stabilator rate', 'rad/s', 'stabilator')
    flap_cmd = g.clip(sch['flap'], 0, 'flap_max').n('flap command', 'rad', 'controls')
    ail_part = inverse(da_cmd, 'flap').n('aileron part of the flaperon command', 'rad', 'controls')
    cmd, rate = {}, {}
    for k, label, part, sgn in FLAPERONS:
        raw = (flap_cmd + ail_part) if sgn > 0 else (flap_cmd - ail_part)
        cmd[k] = g.clip(raw, 'flp_min', 'flp_max').n(f'{label} command', 'rad', part)
        rate[k] = g.clip((cmd[k] - surf[k]) / c('act_tau'), '-surf_rate', 'surf_rate').n(f'{label} rate', 'rad/s', part)
    dr_dot = g.clip((dr_cmd - dr) / c('act_tau'), '-dr_rate', 'dr_rate').n('rudder rate', 'rad/s', 'rudder')
    gear_dot = g.clip((g.clip(sch['gear'], 0, 1) - gear) / c('gear_tau'), '-gear_rate', 'gear_rate').n('landing gear travel rate', '1/s', 'landing_gear')
    flap_pos = (0.5 * (surf['fl'] + surf['fr'])).n('flap position (mean flaperon)', 'rad')
    ail_pos = (0.5 * (surf['fl'] - surf['fr'])).n('aileron position (half the flaperon difference)', 'rad')

    g.subsystem('Propulsion', '')
    thr_dot = ((thr_cmd - thr) / c('eng_tau')).n('d(spool state)/dt', '1/s')

    # =====================================================================================
    # derivatives
    g.derivative(u, u_dot); g.derivative(v, v_dot); g.derivative(w, w_dot)
    g.derivative(p, p_dot); g.derivative(q, q_dot); g.derivative(r, r_dot)
    g.subsystem('Attitude and position', '')
    g.derivative(e0, (-0.5 * (e1 * p + e2 * q + e3 * r) + qfix * e0).n('d(e0)/dt', '1/s'))
    g.derivative(e1, (0.5 * (e0 * p + e2 * r - e3 * q) + qfix * e1).n('d(e1)/dt', '1/s'))
    g.derivative(e2, (0.5 * (e0 * q + e3 * p - e1 * r) + qfix * e2).n('d(e2)/dt', '1/s'))
    g.derivative(e3, (0.5 * (e0 * r + e1 * q - e2 * p) + qfix * e3).n('d(e3)/dt', '1/s'))
    g.derivative(pn, vn); g.derivative(pe, ve); g.derivative(pd, vd)
    g.derivative(chi_u, chi_dot)
    g.derivative(thr, thr_dot)
    g.derivative(de, de_dot)
    for k, _, _, _ in FLAPERONS:
        g.derivative(surf[k], rate[k])
    g.derivative(dr, dr_dot)
    g.derivative(gear, gear_dot)
    g.derivative(de_i, de_i_dot)
    g.derivative(thr_i, thr_i_dot)
    g.derivative(ns_i, ns_i_dot)
    g.derivative(phi_ref, phi_ref_dot)

    # =====================================================================================
    # recorded signals
    O = g.output
    O('pn', pn, 'm'); O('pe', pe, 'm'); O('pd', pd, 'm'); O('height', height, 'm')
    O('e0', e0, '-'); O('e1', e1, '-'); O('e2', e2, '-'); O('e3', e3, '-')
    O('phi', phi, 'rad'); O('theta', theta, 'rad'); O('psi', psi, 'rad'); O('track_unwrapped', chi_u, 'rad')
    O('u', u, 'm/s'); O('v', v, 'm/s'); O('w', w, 'm/s')
    O('p', p, 'rad/s'); O('q', q, 'rad/s'); O('r', r, 'rad/s')
    O('u_dot', u_dot, 'm/s2'); O('v_dot', v_dot, 'm/s2'); O('w_dot', w_dot, 'm/s2')
    O('p_dot', p_dot, 'rad/s2'); O('q_dot', q_dot, 'rad/s2'); O('r_dot', r_dot, 'rad/s2')
    O('vn', vn, 'm/s'); O('ve', ve, 'm/s'); O('vd', vd, 'm/s')
    O('alpha', alpha, 'rad', PART_AIRDATA); O('beta', beta, 'rad', PART_AIRDATA); O('mach', mach, '-', PART_AIRDATA)
    O('tas', vt, 'm/s', PART_AIRDATA); O('qbar', qbar, 'Pa', PART_AIRDATA); O('rho', rho, 'kg/m3'); O('speed_of_sound', a_snd, 'm/s')
    O('nz', nz, 'g', PART_CG); O('ny', ny, 'g', PART_CG); O('nx', nx, 'g', PART_CG)
    O('stabilator', de, 'rad', 'stabilator'); O('stabilator_cmd', stab_cmd, 'rad', 'stabilator'); O('stabilator_rate', de_dot, 'rad/s', 'stabilator')
    names = dict(fl='flaperon_left', fr='flaperon_right')
    for k, _, part, _ in FLAPERONS:
        O(names[k], surf[k], 'rad', part); O(names[k] + '_cmd', cmd[k], 'rad', part); O(names[k] + '_rate', rate[k], 'rad/s', part)
    O('flap', flap_pos, 'rad', 'controls'); O('aileron', ail_pos, 'rad', 'controls'); O('flap_cmd', flap_cmd, 'rad', 'controls')
    O('gear', gear, '-', 'landing_gear'); O('gear_rate', gear_dot, '1/s', 'landing_gear')
    O('cd_induced_controls', cd_ind, '-', PART_MRP); O('cd_profile_controls', cd_prof, '-', PART_MRP); O('cd_gear', cd_lg, '-', 'landing_gear')
    O('rudder', dr, 'rad', 'rudder'); O('rudder_cmd', dr_cmd, 'rad', 'rudder'); O('rudder_cmd_unsat', dr_unsat, 'rad', 'rudder')
    O('rudder_rate', dr_dot, 'rad/s', 'rudder')
    O('elevator_cmd_unsat', de_unsat, 'rad'); O('elevator_cmd', de_cmd, 'rad')
    O('aileron_cmd_unsat', da_unsat, 'rad'); O('aileron_cmd', da_cmd, 'rad')
    O('throttle', thr_cmd, '-', PART_ENGINE); O('spool', thr, '-', PART_ENGINE); O('thrust', thrust, 'N', PART_ENGINE)
    O('thrust_available', t_avail, 'N', PART_ENGINE)
    O('cl', cl, '-', PART_MRP); O('cl_table', cl_t, '-', PART_MRP); O('cd', cd, '-', PART_MRP); O('cm', cm, '-', PART_MRP)
    O('cy', cy, '-', PART_MRP); O('cl_roll', cll, '-', PART_MRP); O('cn', cn, '-', PART_MRP)
    O('lift', lift, 'N', PART_MRP); O('drag', drag, 'N', PART_MRP)
    O('aero_fx', xa, 'N', PART_MRP); O('aero_fy', ya, 'N', PART_MRP); O('aero_fz', za, 'N', PART_MRP)
    O('aero_l_ref', l_ref, 'N m', PART_MRP); O('aero_m_ref', m_ref, 'N m', PART_MRP); O('aero_n_ref', n_ref, 'N m', PART_MRP)
    O('weight_x', gx, 'N', PART_CG); O('weight_y', gy, 'N', PART_CG); O('weight_z', gz, 'N', PART_CG)
    O('force_x', fx, 'N', PART_CG); O('force_y', fy, 'N', PART_CG); O('force_z', fz, 'N', PART_CG)
    O('moment_l', l_cg, 'N m', PART_CG); O('moment_m', m_cg, 'N m', PART_CG); O('moment_n', n_cg, 'N m', PART_CG)
    O('track_cmd', chi_cmd, 'rad', PART_FCC); O('track_error', e_psi, 'rad', PART_FCC)
    O('bank_cmd', phi_cmd, 'rad', PART_FCC); O('nz_cmd', nz_cmd, 'g', PART_FCC); O('nz_available', n_av, 'g', PART_FCC)
    O('nz_speed_hold', n_spd, 'g', PART_FCC); O('nz_alpha_limit', n_alpha_lim, 'g', PART_FCC); O('nz_cap', n_cap, 'g', PART_FCC)
    O('sustained_nz_integrator', ns_i, 'g', PART_FCC); O('nz_thrust_feedforward', n_ff, 'g', PART_FCC); O('nv_demand', nv, 'g', PART_FCC)
    O('pull_flag', pull_flag, '-', PART_FCC); O('thrust_flag', thrust_flag, '-', PART_FCC)
    O('nz_error', e_nz, 'g', PART_FCC); O('alpha_margin_g', e_al, 'g', PART_FCC); O('alpha_low_margin_g', e_al_lo, 'g', PART_FCC)
    O('pitch_integrator', de_i, 'rad', PART_FCC); O('throttle_integrator', thr_i, '-', PART_FCC)
    O('roll_rate_cmd', p_cmd, 'rad/s', PART_FCC); O('turn_flag', turn_flag, '-', PART_FCC)
    O('roll_rate_limit', p_lim, 'rad/s', PART_FCC)
    O('bank_reference', phi_ref, 'rad', PART_FCC)
    O('airspeed_cmd', v_cmd, 'm/s', PART_FCC); O('height_cmd', sch['h'], 'm', PART_FCC); O('climb_rate_cmd', hd_cmd, 'm/s', PART_FCC)
    O('sideslip_cmd', sch['beta'], 'rad', PART_FCC)
    O('mode_bank', sch['sel_bank'], '-', PART_FCC); O('mode_roll_rate', sch['sel_rate'], '-', PART_FCC)
    O('mode_load_factor', sch['sel_nz'], '-', PART_FCC); O('mode_throttle', sch['sel_thr'], '-', PART_FCC)
    O('quat_norm2', qnorm2, '-'); O('climb_rate', climb, 'm/s')
    return g


OPERATOR_KEYS = ('Operator', 'Function', 'Inputs', 'SourceBlock')


def main():
    g = build()
    mdl = HERE / f'{NAME}.mdl'
    g.write_mdl(mdl, stop=60, step=STEP)
    sig = g.signals_manifest()
    (HERE / 'signals.json').write_text(json.dumps(sig, indent=1))
    wiring = g.wiring_manifest()
    names = set()
    for d in g.nodes:
        for k, val in d['params'].items():
            if k in OPERATOR_KEYS:
                continue
            names.update(re.findall(r'(?<![0-9.A-Za-z_])[A-Za-z_][A-Za-z_0-9]*', val))
    arrays = sorted({SCHEDULE_TIME} | {v[0] for v in SCHEDULES.values()})
    scalars = sorted(names - set(arrays))
    (HERE / 'variables.json').write_text(json.dumps(dict(scalars=scalars, arrays=arrays,
                                                         schedules={k: dict(variable=v[0], unit=v[1], what=v[2]) for k, v in SCHEDULES.items()},
                                                         schedule_time=SCHEDULE_TIME), indent=1))
    wiring = dict(model=NAME, mdl=mdl.name, mdl_sha256=hashlib.sha256(mdl.read_bytes()).hexdigest(), n_knot=N_KNOT,
                  id_rule='signal ID in an Unlinked trace = "<subsystem SID>/<block SID>"', **wiring)
    (HERE / 'wiring_graph.json').write_text(json.dumps(wiring, separators=(',', ':')))
    cnt = wiring['counts']
    print(f"{NAME}: {cnt['blocks']} blocks, {cnt['connections']} connections, {cnt['subsystems']} subsystems, {cnt['states']} states, "
          f"{cnt['boundary_ports']} boundary ports, {len(scalars)} scalar and {len(arrays)} vector workspace variables, {len(sig)} recorded signals")
    print(cnt['types'])
    return g


if __name__ == '__main__':
    main()
