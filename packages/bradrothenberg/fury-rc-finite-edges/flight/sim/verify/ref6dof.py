"""Independent Python implementation of the equations in ../MODEL_CONTRACT.md (Fury 6-DOF model).

Written by hand in vector form (rotation matrix from the quaternion, cross products, the 3 x 3 inertia tensor solved
with numpy, coefficient tables and command tables by np.interp on the knot values). It shares no code with the block
graph in ../model/build_model.py, which writes the same equations as scalar blocks with hinge-form tables. It reads
the same parameter file. It is used for
  - the trim solution and the controller initial states (../params.py),
  - the comparison of traces with the Unlinked run (verify.py).

Ported from an earlier flight study by the same author with the Fury's controls: stabilator, two
flaperons (flap and aileron), rudder, landing gear travel.
"""
from __future__ import annotations

import math

import numpy as np

STATE_NAMES = ['u', 'v', 'w', 'p', 'q', 'r', 'e0', 'e1', 'e2', 'e3', 'pn', 'pe', 'pd', 'track_unwrapped', 'spool',
               'stabilator', 'flaperon_left', 'flaperon_right', 'rudder', 'gear',
               'pitch_integrator', 'throttle_integrator', 'sustained_nz_integrator', 'bank_reference']
STATE_INIT = ['u0', 'v0', 'w0', 'p0', 'q0', 'r0', 'e0_0', 'e1_0', 'e2_0', 'e3_0', 'pn0', 'pe0', 'pd0', 'chi0', 'thr0',
              'de0', 'dfl0', 'dfr0', 'dr0', 'gear0', 'dei0', 'thri0', 'nsi0', 'phir0']
IX = {n: i for i, n in enumerate(STATE_NAMES)}
N_STATE = len(STATE_NAMES)
KINEMATIC = (10, 11, 12, 13)          # position and track angle: they move in trimmed flight
R_AIR, GAMMA, T0, P0, LAPSE, RHO0 = 287.05287, 1.4, 288.15, 101325.0, 0.0065, 1.225
CHANNELS = ('chi', 'phi', 'p', 'sel_bank', 'sel_rate', 'n_turn', 'h', 'vs_max', 'nz', 'sel_nz', 'mach', 'tas', 'thr', 'sel_thr', 'beta', 'flap', 'gear')


def isa(h):
    """Temperature K, pressure Pa, density kg/m3, speed of sound m/s (troposphere, held above 11 km)."""
    hc = min(max(h, -500.0), 11000.0)
    t = T0 - LAPSE * hc
    p = P0 * (t / T0) ** 5.255877
    return t, p, p / (R_AIR * t), math.sqrt(GAMMA * R_AIR * t)


def thrust_lapse(P, h, mach):
    """Thrust available / sea-level static thrust, the two algebraic forms of the model."""
    t_air, p_air, rho, _ = isa(h)
    ram = 1.0 + 0.2 * mach * mach
    th0, dl0 = (t_air / T0) * ram, (p_air / P0) * ram ** 3.5
    matt = dl0 * (1.0 - P['eng_k_m'] * math.sqrt(mach) - P['eng_k_theta'] * max(th0 - P['eng_tr'], 0.0)
                  / (P['eng_c_t'] * th0 + P['eng_c_0'] + P['eng_c_m'] * mach))
    dens = (rho / RHO0) ** P['eng_n_sig'] * (1.0 + P['eng_a1'] * mach + P['eng_a2'] * mach * mach)
    return P['eng_w_matt'] * matt + P['eng_w_dens'] * dens


def rot(e):
    """Body-to-NED rotation matrix of the unit quaternion e = (e0, e1, e2, e3), scalar first."""
    e0, ev = e[0], np.asarray(e[1:4])
    k = np.array([[0.0, -ev[2], ev[1]], [ev[2], 0.0, -ev[0]], [-ev[1], ev[0], 0.0]])
    return (e0 * e0 - ev @ ev) * np.eye(3) + 2.0 * np.outer(ev, ev) + 2.0 * e0 * k


def clip(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def soft(d, k1, k2, brk):
    """Large-deflection effectiveness: slope k1 up to the break, k1 - k2 beyond."""
    return k1 * d - k2 * math.copysign(max(abs(d) - brk, 0.0), d)


class Model:
    def __init__(self, params, aero=True, thrust=True, gravity=True, controls=True):
        self.P = P = dict(params['workspace'])
        t = params['tables']
        self.ak = np.array(t['alpha_rad'])
        self.cl_k, self.cd_k, self.cm_k = np.array(t['cl']), np.array(t['cd_remainder']), np.array(t['cm'])
        cmd = params['commands']
        self.ct = np.array(cmd['t'], float)
        self.cy = {k: np.array(cmd[k], float) for k in CHANNELS}
        self.J = np.array([[P['ixx'], 0.0, -P['ixz']], [0.0, P['iyy'], 0.0], [-P['ixz'], 0.0, P['izz']]])
        self.r_mrp = np.array([P['mrp_x'], 0.0, P['mrp_z']])
        self.r_eng = np.array([0.0, 0.0, P['eng_z']])
        self.on = dict(aero=aero, thrust=thrust, gravity=gravity, controls=controls)

    def x0(self):
        return np.array([self.P[k] for k in STATE_INIT], float)

    def breaks(self, stop):
        """Times inside (0, stop) where a command has a kink or a step."""
        ts = [float(t) for t in self.ct if 0.0 < t < stop]
        if 0.0 < self.P['t_turn'] < stop:
            ts.append(float(self.P['t_turn']))
        return sorted(set(ts))

    def command(self, t):
        return {k: float(np.interp(t, self.ct, y)) for k, y in self.cy.items()}

    # ---- everything at one instant
    def eval(self, t, x, step_after=None):
        """step_after: None takes the track step as the block does (after for t >= t_turn); True/False forces it."""
        P = self.P
        vb, om, e = x[0:3], x[3:6], x[6:10]
        pd, chi_u, thr = x[12], x[13], x[14]
        de, dfl, dfr, dr, gear = x[15], x[16], x[17], x[18], x[19]
        de_i, thr_i, ns_i, phi_ref = x[20], x[21], x[22], x[23]
        C = rot(e)
        vned = C @ vb
        h = -pd
        t_air, p_air, rho, a = isa(h)
        v2 = float(vb @ vb)
        vt = max(math.sqrt(v2), 1.0)
        alpha = math.atan2(vb[2], vb[0])
        beta = math.asin(clip(vb[1] / vt, -1.0, 1.0))
        qbar = 0.5 * rho * v2
        mach = vt / a
        S, cref, b, m, g0 = P['s_ref'], P['c_ref'], P['b_ref'], P['mass'], P['g0']

        # ---- aerodynamics about the moment reference point
        e_s = soft(de, P['stab_k1'], P['stab_k2'], P['stab_break'])
        e_l, e_r = (soft(d, P['flap_k1'], P['flap_k2'], P['flap_break']) for d in (dfl, dfr))
        flap_e, ail_e = 0.5 * (e_l + e_r), 0.5 * (e_l - e_r)
        prof = np.array([math.sin(de) ** 2, 0.5 * (math.sin(dfl) ** 2 + math.sin(dfr) ** 2), math.sin(dr) ** 2])
        at = clip(alpha, self.ak[0], self.ak[-1])
        clt, cdr, cmt = (float(np.interp(at, self.ak, y)) for y in (self.cl_k, self.cd_k, self.cm_k))
        hat = np.array([om[0] * b, om[1] * cref, om[2] * b]) / (2.0 * vt)
        cl = clt + P['cl_q'] * hat[1] + P['cl_de'] * e_s + P['cl_df'] * flap_e
        cd_ind = P['cd_de1'] * clt * e_s + P['cd_de3'] * e_s ** 2 + P['cd_df1'] * clt * flap_e + P['cd_df3'] * flap_e ** 2
        cd_prof = np.array([P['cd_de2'], P['cd_df2'], P['cd_dr2']]) @ prof
        cd_gear = P['cd_gear'] * gear
        cd = cdr + P['cd_pol_k'] * clt ** 2 + cd_ind + cd_prof + cd_gear       # the drag table holds the remainder to the parabolic polar
        cm = cmt + P['cm_q'] * hat[1] + P['cm_de'] * e_s + P['cm_df'] * flap_e + P['cm_gear'] * gear
        cy = P['cy_b'] * beta + P['cy_p'] * hat[0] + P['cy_r'] * hat[2] + P['cy_da'] * ail_e + P['cy_dr'] * dr
        cll = ((P['cll_b0'] + P['cll_b1'] * clt) * beta + P['cll_p'] * hat[0] + (P['cll_r0'] + P['cll_r1'] * clt) * hat[2]
               + P['cll_da'] * ail_e + P['cll_dr'] * dr)
        cn = ((P['cn_b0'] + P['cn_b1'] * clt ** 2) * beta + (P['cn_p0'] + P['cn_p1'] * clt) * hat[0] + (P['cn_r0'] + P['cn_r1'] * clt ** 2) * hat[2]
              + P['cn_da'] * ail_e + P['cn_dr'] * dr)
        sa, ca = math.sin(alpha), math.cos(alpha)
        stab_to_body = np.array([[ca, 0.0, -sa], [0.0, 1.0, 0.0], [sa, 0.0, ca]])
        f_aero = qbar * S * (stab_to_body @ np.array([-cd, cy, -cl]))
        m_ref = qbar * S * np.array([b * cll, cref * cm, b * cn])
        if not self.on['aero']:
            f_aero, m_ref = np.zeros(3), np.zeros(3)
        m_aero = m_ref + np.cross(self.r_mrp, f_aero)

        # ---- propulsion
        t_avail = P['t_sls'] * thrust_lapse(P, h, mach)
        f_thr = np.array([thr * t_avail, 0.0, 0.0]) if self.on['thrust'] else np.zeros(3)
        m_thr = np.cross(self.r_eng, f_thr)

        # ---- gravity, rigid body
        f_grav = (m * g0 * (C.T @ np.array([0.0, 0.0, 1.0]))) if self.on['gravity'] else np.zeros(3)
        force = f_aero + f_thr + f_grav
        moment = m_aero + m_thr
        vb_dot = force / m - np.cross(om, vb)
        om_dot = np.linalg.solve(self.J, moment - np.cross(om, self.J @ om))
        n_load = (f_aero + f_thr) / (m * g0)
        nz = -f_aero[2] / (m * g0)
        Om = np.array([[0.0, -om[0], -om[1], -om[2]], [om[0], 0.0, om[2], -om[1]], [om[1], -om[2], 0.0, om[0]], [om[2], om[1], -om[0], 0.0]])
        e_dot = 0.5 * (Om @ e) + P['quat_lambda'] * (1.0 - float(e @ e)) * e
        c31, c32, c33 = C[2]
        a_ned = C @ (force / m)
        chi_dot = float(np.cross(vned * [1, 1, 0], a_ned * [1, 1, 0])[2]) / max(float(vned[:2] @ vned[:2]), 1.0)
        phi = math.atan2(c32, c33)
        climb = -vned[2]

        # ---- commands
        K = self.command(t)
        after = (t >= P['t_turn']) if step_after is None else step_after
        chi_cmd = K['chi'] + (P['chi_turn'] if after else 0.0)
        sel_lat = max(K['sel_bank'], K['sel_rate'])

        # ---- guidance (sensors are ideal taps)
        wgt = m * g0
        qs = qbar * S
        e_psi = (1.0 - sel_lat) * (chi_cmd - chi_u)
        n_alpha_lim = P['k_av'] * qs * P['fcs_cl_lim'] / wgt
        n_cap = min(n_alpha_lim, P['k_bank'] * P['nz_lim'], K['n_turn'])
        n_ff = qs * math.sqrt(max(t_avail / qs - P['fcs_cd0'], 0.0) / P['fcs_cdk']) / wgt
        v_cmd = K['mach'] * a + K['tas']
        v_err = vt - v_cmd
        turn_flag = clip((abs(e_psi) - P['e_thr_on']) / P['e_thr_band'], 0.0, 1.0)
        n_spd_unsat = n_ff + ns_i + P['k_ns_p'] * v_err
        n_spd_lim = clip(n_spd_unsat, P['n_av_min'], 2.0 * P['nz_lim'])
        n_spd = P['hold_speed'] * n_spd_lim + (1.0 - P['hold_speed']) * 2.0 * P['nz_lim']
        n_av = min(max(min(n_cap, n_spd), P['n_av_min']), P['nz_lim'])
        thrust_flag = clip((n_cap - n_spd) / P['dn_thr'] + 1.0, 0.0, 1.0)
        hd_cmd = min(max(P['k_h'] * (K['h'] - h) / P['k_hd'], -K['vs_max']), K['vs_max'])
        nv = P['nv0'] + clip(P['k_hd'] * (hd_cmd - climb), -P['nv_band'], P['nv_band'])
        n_bank = max(nz, min(nz + P['dn_lead'], n_av))
        n_bank_f = max(n_bank, P['n_av_min'])
        nvb = min(P['nv_band'], P['k_nvb'] * (n_bank_f - 1.0))
        nv_b = P['nv0'] + clip(P['k_hd'] * (hd_cmd - climb), -nvb, nvb)
        phi_turn = math.acos(clip(nv_b / n_bank_f, 0.0, 1.0))
        qsb = qs * b
        b2v = b / (2.0 * vt)
        cl_on = clip(nz * m * g0 / qs, 0.0, P['fcs_cl_cap'])
        cl_pl = clip(n_bank_f * m * g0 / qs, 0.0, P['fcs_cl_cap'])
        l_p = qsb * b2v * P['fcs_cll_p'] / P['ixx']
        l_r = qsb * b2v * (P['fcs_cll_r0'] + P['fcs_cll_r1'] * cl_on) / P['ixx']
        l_da = qsb * P['fcs_cll_da'] / P['ixx']
        l_dr = qsb * P['fcs_cll_dr'] / P['ixx']
        l_b = qsb * (P['fcs_cll_b0'] + P['fcs_cll_b1'] * cl_on) / P['ixx']
        n_b = qsb * (P['fcs_cn_b0'] + P['fcs_cn_b1'] * cl_on ** 2) / P['izz']
        n_r = qsb * b2v * (P['fcs_cn_r0'] + P['fcs_cn_r1'] * cl_on ** 2) / P['izz']
        n_p = qsb * b2v * (P['fcs_cn_p0'] + P['fcs_cn_p1'] * cl_on) / P['izz']
        n_dr = qsb * P['fcs_cn_dr'] / P['izz']
        n_da = qsb * P['fcs_cn_da'] / P['izz']
        n_p_net = qsb * b2v * (P['fcs_cn_p0'] + P['fcs_cn_p1'] * cl_pl) / P['izz'] - n_da * l_p / l_da
        n_p_kin = math.tan(max(alpha, 0.0)) / P['tau_roll']
        p_lim = clip(P['k_pr'] * abs(n_dr) * P['dr_max'] / max(abs(n_p_net) + n_p_kin, 1e-4), P['p_min'], P['p_max'])
        phi_ro = math.acos(clip(math.e ** (-P['k_ro'] * abs(e_psi) * vt * p_lim / g0), 0.0, 1.0))
        phi_want = clip(P['k_psi'] * e_psi, -phi_ro, phi_ro)
        phi_hdg = min(max(phi_want, -phi_turn), phi_turn)
        phi_cmd = (1.0 - K['sel_bank']) * phi_hdg + K['sel_bank'] * K['phi']
        pull_flag = (1.0 - sel_lat) * clip((abs(phi_want) - phi_turn) / P['phi_band'] + 1.0, 0.0, 1.0) * clip(abs(phi_want) / P['phi_band'], 0.0, 1.0)
        c33s = max(c33, P['c33_min'])
        nz_level = nv / c33s
        nz_pull = min(n_av, (nv + min(P['dnv_pull'], nvb)) / c33s)
        nz_auto = pull_flag * nz_pull + (1.0 - pull_flag) * nz_level
        nz_cmd = clip((1.0 - K['sel_nz']) * nz_auto + K['sel_nz'] * K['nz'], P['nz_min'], P['nz_lim'])
        thr_p = m * (v_cmd - vt) / (P['tau_v'] * t_avail)
        pull_prog = clip((nz - 1.0) / (P['k_tp'] * (n_av - 1.0)), 0.0, 1.0)
        n_want = max(nz, turn_flag * pull_flag * pull_prog * n_cap)
        thr_ff = P['fcs_cdk'] * wgt * wgt * (max(n_want * n_want, 1.0) - 1.0) / (qs * t_avail)
        thr_unsat = thr_i + thr_p + thr_ff
        thr_auto = clip(thr_unsat, P['thr_idle'], 1.0)
        ns_i_dot = (turn_flag * (P['k_ns_i'] * v_err + P['k_rel'] * (1.0 - thr_auto) + (n_spd_lim - n_spd_unsat) / P['tau_aw'])
                    - (1.0 - turn_flag) * ns_i / P['tau_ns_reset'])
        thr_cmd = clip((1.0 - K['sel_thr']) * thr_auto + K['sel_thr'] * K['thr'], P['thr_idle'], 1.0)
        thr_pi = thr_i + thr_p
        thr_i_dot = thr_p / P['tau_vi'] + (clip(thr_pi, P['thr_idle'], 1.0) - thr_pi) / P['tau_aw']

        # ---- pitch law
        z_al = qs * P['fcs_cla'] / (m * vt)
        m_al = qs * cref * P['fcs_cma'] / P['iyy']
        m_q = qs * cref * cref * P['fcs_cm_q'] / (2.0 * vt * P['iyy'])
        m_de = qs * cref * P['fcs_cm_de'] / P['iyy']
        n_al = qs * P['fcs_cla'] / wgt
        w_sp, z_sp, p_int = P['w_sp'], P['z_sp'], P['p_int']
        a2, a1, a0 = p_int + 2 * z_sp * w_sp, w_sp ** 2 + 2 * z_sp * w_sp * p_int, p_int * w_sp ** 2
        mq_cl = z_al - a2
        k_q, k_p, k_i = m_q - mq_cl, (a1 + z_al * mq_cl) / n_al, a0 / n_al
        e_nz = nz_cmd - nz
        e_al = n_al * (P['alpha_lim'] - alpha)
        e_al_lo = n_al * (P['alpha_min'] - alpha)
        e_sel = max(min(e_nz, e_al), e_al_lo)
        q_ref = g0 * (nz_cmd - c33) / vt
        de_unsat = de_i - (m_al * alpha + k_q * (om[1] - q_ref) - k_p * e_sel) / m_de
        de_cmd = clip(de_unsat, P['de_min'], P['de_max'])
        de_i_dot = k_i * e_sel / m_de + (de_cmd - de_unsat) / P['tau_aw']

        # ---- roll and yaw laws
        p_hold = clip(P['k_phi'] * (phi_cmd - phi), -p_lim, p_lim)
        e_ref = math.remainder(phi_ref - phi, 2.0 * math.pi)
        p_stick_in = clip(K['p'], -p_lim, p_lim)
        p_stick = clip(P['k_phi'] * e_ref, -p_lim, p_lim) + p_stick_in
        p_cmd = (1.0 - K['sel_rate']) * p_hold + K['sel_rate'] * p_stick
        phi_ref_dot = K['sel_rate'] * p_stick_in - (1.0 - K['sel_rate']) * e_ref / P['tau_ref']
        da_unsat = ((p_cmd - om[0]) / P['tau_roll'] - l_p * om[0] - l_r * om[2] - l_dr * dr - l_b * beta) / l_da
        da_cmd = clip(da_unsat, -P['da_max'], P['da_max'])
        k_b = clip(P['w_dr'] ** 2 - n_b, 0.0, P['kb_max'] * abs(n_dr))
        w_yaw = math.sqrt(max(k_b + n_b, 0.0))
        k_r = clip(2.0 * P['z_dr'] * w_yaw + n_r, 0.0, P['kr_max'] * abs(n_dr))
        r_ref = om[0] * math.tan(alpha) + g0 * c32 / vt
        dr_unsat = (k_b * beta - (k_b + n_b) * K['beta'] - k_r * (om[2] - r_ref) - n_da * da_cmd - n_p * om[0]) / n_dr
        dr_cmd = clip(dr_unsat, -P['dr_max'], P['dr_max'])

        # ---- mixer and actuators
        def inverse(x, kind):          # linear demand to deflection: inverse of the effectiveness curve
            return x + P[kind + '_inv'] * math.copysign(max(abs(x) - P[kind + '_break'], 0.0), x)

        stab_cmd = clip(inverse(de_cmd, 'stab'), P['stab_min'], P['stab_max'])
        flap_cmd = clip(K['flap'], 0.0, P['flap_max'])
        ail = inverse(da_cmd, 'flap')
        fl_cmd = clip(flap_cmd + ail, P['flp_min'], P['flp_max'])
        fr_cmd = clip(flap_cmd - ail, P['flp_min'], P['flp_max'])
        gear_cmd = clip(K['gear'], 0.0, 1.0)
        if not self.on['controls']:
            stab_cmd, fl_cmd, fr_cmd, dr_cmd, thr_cmd, gear_cmd = de, dfl, dfr, dr, thr, gear
            de_i_dot = thr_i_dot = ns_i_dot = phi_ref_dot = 0.0
        rate = lambda cmd_, pos: clip((cmd_ - pos) / P['act_tau'], -P['surf_rate'], P['surf_rate'])
        s_dot = [rate(stab_cmd, de), rate(fl_cmd, dfl), rate(fr_cmd, dfr)]
        dr_dot = clip((dr_cmd - dr) / P['act_tau'], -P['dr_rate'], P['dr_rate'])
        gear_dot = clip((gear_cmd - gear) / P['gear_tau'], -P['gear_rate'], P['gear_rate'])
        thr_dot = (thr_cmd - thr) / P['eng_tau']

        xdot = np.concatenate([vb_dot, om_dot, e_dot, vned, [chi_dot, thr_dot], s_dot, [dr_dot, gear_dot, de_i_dot, thr_i_dot, ns_i_dot, phi_ref_dot]])
        out = dict(u_dot=vb_dot[0], v_dot=vb_dot[1], w_dot=vb_dot[2], p_dot=om_dot[0], q_dot=om_dot[1], r_dot=om_dot[2],
                   vn=vned[0], ve=vned[1], vd=vned[2], height=h, alpha=alpha, beta=beta, mach=mach, tas=vt, qbar=qbar, rho=rho,
                   speed_of_sound=a, nz=nz, ny=n_load[1], nx=n_load[0], phi=phi, theta=math.asin(clip(-c31, -1.0, 1.0)),
                   psi=math.atan2(C[1, 0], C[0, 0]),
                   flap=0.5 * (dfl + dfr), aileron=0.5 * (dfl - dfr), flap_cmd=flap_cmd,
                   elevator_cmd_unsat=de_unsat, elevator_cmd=de_cmd, aileron_cmd_unsat=da_unsat, aileron_cmd=da_cmd,
                   rudder_cmd_unsat=dr_unsat, rudder_cmd=dr_cmd,
                   stabilator_cmd=stab_cmd, stabilator_rate=s_dot[0], flaperon_left_cmd=fl_cmd, flaperon_right_cmd=fr_cmd,
                   flaperon_left_rate=s_dot[1], flaperon_right_rate=s_dot[2], gear_rate=gear_dot,
                   cd_induced_controls=cd_ind, cd_profile_controls=cd_prof, cd_gear=cd_gear,
                   rudder_rate=dr_dot, throttle=thr_cmd, thrust=f_thr[0], thrust_available=t_avail,
                   cl=cl, cl_table=clt, cd=cd, cm=cm, cy=cy, cl_roll=cll, cn=cn, lift=qs * cl, drag=qs * cd,
                   aero_fx=f_aero[0], aero_fy=f_aero[1], aero_fz=f_aero[2], aero_l_ref=m_ref[0], aero_m_ref=m_ref[1], aero_n_ref=m_ref[2],
                   weight_x=f_grav[0], weight_y=f_grav[1], weight_z=f_grav[2], force_x=force[0], force_y=force[1], force_z=force[2],
                   moment_l=moment[0], moment_m=moment[1], moment_n=moment[2], track_cmd=chi_cmd, track_error=e_psi,
                   bank_cmd=phi_cmd, nz_cmd=nz_cmd, nz_available=n_av, nz_speed_hold=n_spd, nz_thrust_feedforward=n_ff, nz_cap=n_cap,
                   pull_flag=pull_flag, thrust_flag=thrust_flag, nz_alpha_limit=n_alpha_lim, nv_demand=nv, nz_error=e_nz,
                   alpha_margin_g=e_al, alpha_low_margin_g=e_al_lo, roll_rate_cmd=p_cmd, roll_rate_limit=p_lim, turn_flag=turn_flag,
                   airspeed_cmd=v_cmd, height_cmd=K['h'], climb_rate_cmd=hd_cmd, sideslip_cmd=K['beta'],
                   mode_bank=K['sel_bank'], mode_roll_rate=K['sel_rate'], mode_load_factor=K['sel_nz'], mode_throttle=K['sel_thr'],
                   quat_norm2=float(e @ e), climb_rate=climb,
                   k_p=k_p, k_q=k_q, k_i=k_i, m_alpha=m_al, m_delta=m_de)
        return xdot, out

    def rhs(self, t, x, step_after=None):
        return self.eval(t, x, step_after)[0]

    # ---- integration
    def simulate(self, stop, dt_out, x0=None, rtol=1e-10, atol=1e-12, max_step=0.01):
        """scipy DOP853 with tight tolerances; integration is restarted at the track step and at every kink of a command
        table, so no step straddles a discontinuity. Returns time and a dict of arrays (states and outputs)."""
        from scipy.integrate import solve_ivp
        x = self.x0() if x0 is None else np.array(x0, float)
        n = int(round(stop / dt_out))
        t_out = np.arange(n + 1) * dt_out
        edges = [0.0] + self.breaks(stop) + [stop]
        X = np.zeros((n + 1, len(x)))
        for a, b in zip(edges[:-1], edges[1:]):
            sel = (t_out >= a - 1e-12) & (t_out <= b + 1e-12)
            after = bool(a >= self.P['t_turn'] - 1e-12)
            sol = solve_ivp(lambda t, y: self.rhs(t, y, after), (a, b), x, method='DOP853', rtol=rtol, atol=atol,
                            max_step=max_step, t_eval=np.clip(t_out[sel], a, b))
            assert sol.success, sol.message
            X[sel] = sol.y.T
            x = sol.y[:, -1]
        return t_out, self.collect(t_out, X)

    def simulate_rk4(self, stop, dt, x0=None, start=0.0):
        """Classical fixed-step RK4, the scheme the Unlinked run uses (for a like-for-like check)."""
        x = self.x0() if x0 is None else np.array(x0, float)
        n = int(round((stop - start) / dt))
        X = np.zeros((n + 1, len(x)))
        X[0] = x
        tt = self.P['t_turn']
        for k in range(n):
            t = start + k * dt
            after = bool(t >= tt - 1e-9)
            k1 = self.rhs(t, x, after)
            k2 = self.rhs(t + dt / 2, x + dt / 2 * k1, after)
            k3 = self.rhs(t + dt / 2, x + dt / 2 * k2, after)
            k4 = self.rhs(t + dt, x + dt * k3, after)
            x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            X[k + 1] = x
        t_out = start + np.arange(n + 1) * dt
        return t_out, self.collect(t_out, X)

    def collect(self, t_out, X):
        data = {n: X[:, i].copy() for i, n in enumerate(STATE_NAMES)}
        outs = None
        tt = self.P['t_turn']
        for k, (t, x) in enumerate(zip(t_out, X)):
            _, o = self.eval(t, x, bool(t >= tt - 1e-9))
            if outs is None:
                outs = {name: np.zeros(len(t_out)) for name in o}
            for name, val in o.items():
                outs[name][k] = val
        data.update(outs)
        return data
