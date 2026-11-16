"""Parameter set of the Fury 6-DOF model for one weight case and one flight condition: workspace of the block graph,
coefficient tables, onboard constants of the control laws and the trimmed start.

    python flight/sim/params.py --case combat --mach 0.6 --alt-ft 15000 [--out file.json]

Everything physical comes from flight/aircraft.py (estimates; see flight/out/aircraft.md). The control-law targets are
those of an earlier flight study by the same author, from which the design rule is ported: the same rule for
every weight and flight condition, no tuning per case. The coefficient tables are those of the entry Mach number and
do not change with Mach number during a run.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

SIM = Path(__file__).resolve().parent
FLIGHT = SIM.parent
sys.path.insert(0, str(FLIGHT))
sys.path.insert(0, str(SIM / 'verify'))
sys.path.insert(0, str(SIM))
import aircraft as fa          # noqa: E402
import schedule                # noqa: E402
from ref6dof import Model, isa, N_STATE, KINEMATIC, soft  # noqa: E402

DEG = math.pi / 180.0
FT, KT, LB, LBF = 0.3048, 0.514444444, 0.45359237, 4.4482216153
N_KNOT = 14
G0 = 9.80665

# Maneuver and control-law constants: identical for every weight and flight condition (values of the earlier study).
COMMON = dict(
    t_turn=1.0e9, chi_turn=0.0, hold_speed=1.0,
    # pitch law targets (closed-loop short period and integrator pole)
    w_sp=3.5, z_sp=0.8, p_int=1.5, tau_aw=0.2,
    # roll law
    tau_roll=0.4, k_phi=2.0, p_max=120.0 * DEG, tau_ref=0.2,
    # yaw law (Dutch roll target)
    w_dr=1.5, z_dr=0.7, kb_max=2.0, kr_max=2.0, k_pr=0.5, p_min=5.0 * DEG,
    # guidance
    k_psi=4.0, k_ro=0.7, k_h=0.01, k_hd=0.04, nv_band=0.5, c33_min=0.15, k_av=1.0, k_bank=1.0, n_av_min=1.02, dn_lead=1.0, dnv_pull=0.2, k_nvb=0.5,
    k_ns_p=0.25, k_ns_i=0.04, tau_ns_reset=2.0, phi_band=10.0 * DEG, dn_thr=0.1, k_rel=0.5, k_tp=0.7,
    tau_v=4.0, tau_vi=8.0, e_thr_on=5.0 * DEG, e_thr_band=5.0 * DEG,
    # landing gear travel: about 6 s from up to down
    gear_tau=0.5, gear_rate=1.0 / 6.0,
    # numerics
    quat_lambda=1.0, g0=G0,
)
COMMON_NOTES = {
    'w_sp, z_sp, p_int': 'closed-loop short-period frequency 3.5 rad/s, damping 0.8, integrator pole 1.5 rad/s (carried over from earlier studies)',
    'p_max': 'largest roll rate command 120 deg/s (ASSUMPTION for a fighter-class aircraft; the rudder-based roll rate limit of the law may hold it lower)',
    'hold_speed': '1: a turn to a track target is cut back to what thrust sustains at the commanded speed; 0: the turn is flown at the load factor asked for '
                  'and the speed is let go (a hard turn that bleeds speed)',
    'k_bank': '1.0: the turn guidance may command the structural limit itself',
    'k_psi': '4.0 (6.0 in the earlier study): bank per track error; with 6 the roll-out of a 7 to 9 g turn came too late, the bank reversed by 30 deg and the '
             'aircraft unloaded to 0 g for a moment; with 4 the roll-out is clean (chosen on the 5, 7 and 9 g turns)',
    'gear_tau, gear_rate': 'ASSUMPTION: the gear travels from up to down in about 6 s',
}


def hinge_form(prefix, ak, y):
    """y(a) = y0 + m0 (a - a0) + sum_i d_i max(a - a_i, 0): the form the block graph evaluates."""
    m = np.diff(y) / np.diff(ak)
    out = {f'{prefix}_0': float(y[0]), f'{prefix}_m0': float(m[0])}
    for i in range(1, len(ak) - 1):
        out[f'{prefix}_d{i}'] = float(m[i] - m[i - 1])
    return out


def design(case='combat', mach=0.6, alt_m=4572.0, commands=None, maneuver='level flight', hold_speed=1.0, gear=0.0, flap_deg=0.0, stores=True, n_turn=None, table_mach=None):
    st = fa.statement()
    A = fa.ASSUME
    table_mach = mach if table_mach is None else table_mach
    aero = fa.Aero(table_mach, stores)
    d = {k: v for k, v in aero.derivatives().items() if k != 'body'}
    tab = aero.table()
    wc = st['weights']['cases'][case]
    ref = st['reference']
    S, cbar, b = ref['s_m2'], ref['c_m'], ref['b_m']
    cg, mrp, eng = np.array(st['balance']['cg_m']), np.array(st['balance']['moment_reference_m']), np.array(st['engine']['thrust_point_m'])
    to_body = lambda pt: [float(-(pt[0] - cg[0])), float(pt[1] - cg[1]), float(-(pt[2] - cg[2]))]
    r_mrp, r_eng = to_body(mrp), to_body(eng)

    knots = np.array(tab['knots_deg'], float)
    assert len(knots) == N_KNOT and np.all(np.diff(knots) > 0), f'the tables need {N_KNOT} increasing knots, got {knots}'
    ak = knots * DEG
    cl_k, cd_k, cm_k = (np.array(tab[n], float) for n in ('cl', 'cd', 'cm'))

    W = dict(COMMON)
    W['hold_speed'] = float(hold_speed)
    W.update(mass=wc['mass_kg'], **wc['inertia'], s_ref=S, c_ref=cbar, b_ref=b, mrp_x=r_mrp[0], mrp_z=r_mrp[2], eng_z=r_eng[2],
             t_sls=st['engine']['thrust_installed_sl_static_N'], **st['engine']['lapse'], act_tau=A['actuator_time_s'], eng_tau=A['spool_time_s'], thr_idle=A['idle_fraction'])
    W.update({f'ak_{i}': float(a) for i, a in enumerate(ak)})
    # Drag: CD = cd_pol_k CL(alpha)^2 + remainder(alpha). A table that is piecewise linear in angle of attack lies above a parabolic polar
    # between its knots, so the parabolic part is evaluated from the lift table and only the remainder is tabulated.
    lo, hi = tab['polar_fit_deg']
    fit = (knots >= lo - 1e-6) & (knots <= hi + 1e-6)
    cd_pol_k = float(np.polyfit(cl_k[fit] ** 2, cd_k[fit], 1)[0])
    cdr_k = cd_k - cd_pol_k * cl_k ** 2
    W['cd_pol_k'] = cd_pol_k
    for prefix, yk in (('cl', cl_k), ('cd', cdr_k), ('cm', cm_k)):
        W.update(hinge_form(prefix, ak, yk))
    W.update({k: float(v) for k, v in d.items()})
    # the laws command a linear surface (effectiveness k1 at every deflection); the mixer turns the demand into the deflection that gives it
    for kind in ('stab', 'flap'):
        W[kind + '_inv'] = d[kind + '_k1'] / (d[kind + '_k1'] - d[kind + '_k2']) - 1.0
    lin = lambda x, kind: soft(x, d[kind + '_k1'], d[kind + '_k2'], d[kind + '_break']) / d[kind + '_k1']
    inv = lambda x, kind: x + W[kind + '_inv'] * math.copysign(max(abs(x) - d[kind + '_break'], 0.0), x)
    stab = [x * DEG for x in A['stabilator_deg']]
    flp = [x * DEG for x in A['flaperon_deg']]
    W.update(stab_min=stab[0], stab_max=stab[1], de_min=lin(stab[0], 'stab'), de_max=lin(stab[1], 'stab'), flp_min=flp[0], flp_max=flp[1],
             flap_max=A['flap_landing_deg'] * DEG, da_max=lin(min(flp[1], -flp[0]), 'flap'),
             surf_rate=A['surface_rate_dps'] * DEG, dr_max=A['rudder_deg'] * DEG, dr_rate=A['rudder_rate_dps'] * DEG,
             nz_lim=A['n_limit'], nz_min=A['n_min'], alpha_lim=tab['alpha_lim_deg'] * DEG, alpha_min=tab['alpha_min_deg'] * DEG)

    # ---- steady, trimmed coefficients about the centre of gravity (for the onboard constants)
    flap0 = flap_deg * DEG
    eff_f0 = soft(flap0, d['flap_k1'], d['flap_k2'], d['flap_break'])

    def coeff(a, de_lin, gear_=0.0, eff_f=0.0, flap_=0.0):
        """CL, CD, Cm about the CG at an angle of attack [rad] and a linear stabilator demand (no pitch rate, no thrust)."""
        e_s = d['stab_k1'] * de_lin
        de_real = inv(de_lin, 'stab')
        clt, cdt, cmt = (float(np.interp(a, ak, y)) for y in (cl_k, cd_k, cm_k))
        clv = clt + d['cl_de'] * e_s + d['cl_df'] * eff_f
        cdv = (cdt + d['cd_de1'] * clt * e_s + d['cd_de3'] * e_s ** 2 + d['cd_de2'] * math.sin(de_real) ** 2
               + d['cd_df1'] * clt * eff_f + d['cd_df3'] * eff_f ** 2 + d['cd_df2'] * math.sin(flap_) ** 2 + d['cd_gear'] * gear_)
        cmv = cmt + d['cm_de'] * e_s + d['cm_df'] * eff_f + d['cm_gear'] * gear_
        cx, cz = clv * math.sin(a) - cdv * math.cos(a), -cdv * math.sin(a) - clv * math.cos(a)
        return clv, cdv, cmv + (r_mrp[2] * cx - r_mrp[0] * cz) / cbar

    def trimmed_point(a, qs, thrust):
        """Stabilator demand for zero pitching moment about the CG at an angle of attack, with the thrust-line moment; returns CL, CD, demand."""
        cm_t = r_eng[2] * thrust / (qs * cbar)
        x = 0.0
        for _ in range(30):
            f0 = coeff(a, x)[2] + cm_t
            f1 = coeff(a, x + 1e-4)[2] + cm_t
            x -= f0 / ((f1 - f0) / 1e-4)
        clv, cdv, _ = coeff(a, x)
        return clv, cdv, x

    cm_de_cg = (coeff(4.0 * DEG, 0.01)[2] - coeff(4.0 * DEG, 0.0)[2]) / 0.01
    W.update(fcs_cla=1.0, fcs_cma=0.0, fcs_cl_lim=1.0, fcs_cm_de=cm_de_cg, fcs_cm_q=d['cm_q'], fcs_cll_p=d['cll_p'],
             fcs_cll_da=d['flap_k1'] * d['cll_da'], fcs_cll_dr=d['cll_dr'], fcs_cn_dr=d['cn_dr'], fcs_cn_da=d['flap_k1'] * d['cn_da'],
             fcs_cll_b0=d['cll_b0'], fcs_cll_b1=d['cll_b1'], fcs_cll_r0=d['cll_r0'], fcs_cll_r1=d['cll_r1'],
             fcs_cn_b0=d['cn_b0'], fcs_cn_b1=d['cn_b1'], fcs_cn_r0=d['cn_r0'], fcs_cn_r1=d['cn_r1'],
             fcs_cn_p0=d['cn_p0'], fcs_cn_p1=d['cn_p1'], fcs_cl_cap=float(tab['cl_max']), fcs_cd0=0.02, fcs_cdk=cd_pol_k)

    # ---- trim: level flight, wings level, at the Mach number and height (gear and flap as given)
    t_air, p_air, rho, a_snd = isa(alt_m)
    vt = mach * a_snd
    qbar = 0.5 * rho * vt * vt
    W.update(v0=0.0, p0=0.0, q0=0.0, r0=0.0, pn0=0.0, pe0=0.0, pd0=-alt_m, chi0=0.0, dr0=0.0, e1_0=0.0, e3_0=0.0,
             nv0=1.0, dei0=0.0, nsi0=0.0, phir0=0.0, thri0=0.5, thr0=0.5, u0=vt, w0=0.0, e0_0=1.0, e2_0=0.0, de0=0.0, dfl0=flap0, dfr0=flap0, gear0=float(gear))
    tables = dict(alpha_rad=ak.tolist(), cl=cl_k.tolist(), cd=cd_k.tolist(), cd_remainder=cdr_k.tolist(), cd_polar_k=cd_pol_k, cm=cm_k.tolist(),
                  cd_rule='CD(alpha) = cd_polar_k CL(alpha)^2 + remainder(alpha); CL, remainder and Cm piecewise linear between the knots; cd lists the knot values of CD')
    cmd0 = schedule.Commands(W, mach, alt_m, n_turn=n_turn).tables()
    params = dict(workspace=W, tables=tables, commands=cmd0)

    def set_state(z):
        alpha, de_real, thr = z
        W.update(u0=vt * math.cos(alpha), w0=vt * math.sin(alpha), e0_0=math.cos(alpha / 2), e2_0=math.sin(alpha / 2), de0=de_real, thr0=thr, thri0=thr)

    def residual(z):
        set_state(z)
        mdl = Model(params, controls=False)
        xd, _ = mdl.eval(0.0, mdl.x0())
        return np.array([xd[0], xd[2], xd[4]])

    from scipy.optimize import fsolve
    z, info, ok, msg = fsolve(residual, [3.0 * DEG, -1.0 * DEG, 0.4], full_output=True, xtol=1e-13)
    if ok != 1 or np.abs(residual(z)).max() > 1e-8:
        z, info, ok, msg = fsolve(residual, [8.0 * DEG, -6.0 * DEG, 0.7], full_output=True, xtol=1e-13)
    set_state(z)
    alpha_t, de_t, thr_t = (float(v) for v in z)
    solved = bool(ok == 1 and np.abs(residual(z)).max() < 1e-8)
    why_not = [w_ for w_, bad in (
        ('no solution of the three trim equations', not solved),
        (f'throttle {thr_t:.3f} needed: thrust below drag in level flight', solved and thr_t > 1.0),
        ('throttle below zero', solved and thr_t <= 0.0),
        (f'angle of attack {alpha_t / DEG:.2f} deg outside the limiters', solved and not tab['alpha_min_deg'] < alpha_t / DEG < tab['alpha_lim_deg']),
        (f'stabilator {de_t / DEG:.2f} deg outside its travel', solved and not stab[0] < de_t < stab[1])) if bad]

    # onboard slopes of the pitch law: lift slope and pitch stiffness about the CG over the knot interval that holds the 1 g trim angle
    inside = knots[knots <= tab['alpha_cl_max_deg'] + 1e-9]
    i = int(np.clip(np.searchsorted(inside, alpha_t / DEG, side='right') - 1, 0, len(inside) - 2))
    s_lo, s_hi = float(inside[i]), float(inside[i + 1])
    fcs_cla = (coeff(s_hi * DEG, 0.0)[0] - coeff(s_lo * DEG, 0.0)[0]) / ((s_hi - s_lo) * DEG)
    fcs_cma = (coeff(s_hi * DEG, 0.0)[2] - coeff(s_lo * DEG, 0.0)[2]) / ((s_hi - s_lo) * DEG)
    W.update(fcs_cla=fcs_cla, fcs_cma=fcs_cma)
    mdl = Model(params, controls=False)
    _, o = mdl.eval(0.0, mdl.x0())
    W['nv0'] = float(o['nz'] * math.cos(alpha_t))
    t_avail = float(o['thrust_available'])

    # lift limit of the guidance: trimmed lift coefficient at the angle-of-attack limiter (full thrust)
    qs = qbar * S
    cl_lim, cd_lim, de_lim = trimmed_point(W['alpha_lim'], qs, t_avail)
    W['fcs_cl_lim'] = float(cl_lim)
    # onboard drag polar of the guidance: the trimmed clean polar fitted as CD = fcs_cd0 + fcs_cdk CL^2 between 1 g and the limiter
    pts = [trimmed_point(al, qs, t_avail) for al in np.linspace(min(alpha_t, W['alpha_lim'] - 3.0 * DEG), W['alpha_lim'], 60)]
    clp, cdp = np.array([pt[0] for pt in pts]), np.array([pt[1] for pt in pts])
    kfit, c0fit = np.polyfit(clp ** 2, cdp, 1)
    W['fcs_cdk'], W['fcs_cd0'] = float(kfit), float(max(c0fit, 0.005))

    W['thr0'] = W['thri0'] = thr_t
    params['commands'] = commands if commands is not None else schedule.Commands(W, mach, alt_m, n_turn=n_turn).tables()
    # controller initial state: the pitch integrator holds the trim stabilator demand
    mdl = Model(params)
    _, o = mdl.eval(0.0, mdl.x0(), step_after=False)
    W['dei0'] = float(lin(de_t, 'stab') - o['elevator_cmd_unsat'])
    mdl = Model(params)
    xd, o = mdl.eval(0.0, mdl.x0(), step_after=False)

    wgt = W['mass'] * G0
    trim = dict(ok=not why_not, why_not=why_not, mach=mach, height_m=alt_m, tas_m_s=vt, qbar_Pa=qbar, alpha_deg=alpha_t / DEG, stabilator_deg=de_t / DEG,
                throttle=thr_t, thrust_N=float(o['thrust']), thrust_available_N=t_avail, cl=float(o['cl']), cd=float(o['cd']), lift_to_drag=float(o['cl'] / o['cd']),
                residual_max_abs=float(max(abs(xd[i]) for i in range(N_STATE) if i not in KINEMATIC)),
                gear=float(gear), flap_deg=flap_deg,
                us_customary=dict(speed_kt=round(vt / KT, 1), altitude_ft=round(alt_m / FT), weight_lb=round(W['mass'] / LB),
                                  wing_loading_lb_ft2=round(wgt / S / (LBF / FT ** 2), 1), thrust_lbf=round(float(o['thrust']) / LBF),
                                  thrust_available_lbf=round(t_avail / LBF)))
    design_rec = dict(
        rule='pitch: the onboard M_alpha is cancelled with the stabilator, then proportional and integral gains on the load-factor error and a pitch-rate gain place '
             'the three poles (from Z_alpha, M_q, M_delta, N_alpha at the current dynamic pressure); roll by model following with time constant tau_roll; yaw gains '
             'to a Dutch-roll target; the same targets for every weight and flight condition',
        fcs_cla_per_rad=fcs_cla, fcs_cma_per_rad=fcs_cma, static_margin_from_tables=-fcs_cma / fcs_cla, slope_interval_deg=[s_lo, s_hi], cm_de_about_cg=cm_de_cg,
        onboard_trimmed_polar=dict(cd0=W['fcs_cd0'], k=W['fcs_cdk']),
        lift_limit=dict(alpha_limiter_deg=W['alpha_lim'] / DEG, cl_table_at_limiter=float(np.interp(W['alpha_lim'], ak, cl_k)), cl_trimmed_at_limiter=float(cl_lim),
                        stabilator_demand_at_limiter_deg=float(de_lim / DEG), load_factor_at_limiter_at_entry_speed=float(qs * cl_lim / wgt)),
        gains_at_trim=dict(k_p=o['k_p'], k_q=o['k_q'], k_i=o['k_i'], m_alpha=o['m_alpha'], m_delta=o['m_delta']))
    anchors = dict(cg=[float(v) for v in cg], wing_reference_point=[float(v) for v in mrp], engine=[float(v) for v in eng])
    return dict(variant='fury', name='Fury model, conventional tail, ' + wc['label'], revision='flight-1', placeholder=False, maneuver=maneuver, case=case,
                condition=dict(mach=mach, altitude_m=alt_m, altitude_ft=alt_m / FT, tas_m_s=vt, tas_kt=vt / KT, flight_mass_kg=wc['mass_kg'], flight_weight_lb=wc['weight_lb']),
                frame='model frame: x aft from the nose, y starboard, z up (metres); body axes of the simulation: x forward, y right, z down, origin at the CG',
                statement='ESTIMATES: weights, balance, inertia, thrust and every aerodynamic coefficient (flight/out/aircraft.md)', common_notes=COMMON_NOTES,
                physical=dict(mass_kg=wc['mass_kg'], inertia_kgm2=wc['inertia'], cg_m=[float(v) for v in cg], reference=ref,
                              moment_ref_from_cg_body_m=r_mrp, thrust_point_from_cg_body_m=r_eng),
                anchors=anchors, tables=dict(alpha_deg=knots.tolist(), **tables),
                tables_info=dict(table_mach=table_mach, alpha_cl_max_deg=tab['alpha_cl_max_deg'], cl_max=tab['cl_max'], alpha_lim_deg=tab['alpha_lim_deg'],
                                 note='the coefficient tables are those of table_mach and do not change with Mach number during a run'), derivatives={k: float(v) for k, v in d.items()}, design=design_rec, trim=trim,
                workspace={k: float(v) for k, v in W.items()}, commands=params['commands'])


def build(case, mach, alt_m, **kw):
    par = design(case, mach, alt_m, **kw)
    need = json.loads((SIM / 'model/variables.json').read_text())['scalars']
    missing = [n for n in need if n not in par['workspace']]
    assert not missing, f'workspace variables missing: {missing}'
    return par


def write_m(par, path, t_far=None):
    """MATLAB-style workspace file (scalars and command vectors) for opening the model in the Unlinked web app."""
    t_far = par['commands']['t'][-1] + 3600.0 if t_far is None else t_far
    vec = schedule.workspace_vectors(par['commands'], t_far)
    m = [f'% Workspace of the Fury 6-DOF model: {par["name"]}, {par["maneuver"]}.',
         '% Written by flight/sim/params.py. SI units, radians. Estimates (flight/out/aircraft.md).']
    m += [f'{n} = {par["workspace"][n]!r};' for n in sorted(par['workspace'])]
    m += [f'{n} = {v};' for n, v in vec.items()]
    Path(path).write_text('\n'.join(m) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--case', default='combat')
    ap.add_argument('--mach', type=float, default=0.6)
    ap.add_argument('--alt-ft', type=float, default=15000.0)
    ap.add_argument('--gear', type=float, default=0.0)
    ap.add_argument('--flap-deg', type=float, default=0.0)
    ap.add_argument('--out')
    a = ap.parse_args()
    par = build(a.case, a.mach, a.alt_ft * FT, gear=a.gear, flap_deg=a.flap_deg)
    out = Path(a.out or SIM / 'params' / f'{a.case}_M{a.mach:.3f}_{a.alt_ft:.0f}ft.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(par, indent=1))
    write_m(par, out.with_suffix('.m'))
    t, L = par['trim'], par['design']['lift_limit']
    print(f"{par['name']} Mach {a.mach:.3f} at {a.alt_ft:,.0f} ft: trim ok={t['ok']} {t['why_not']} alpha {t['alpha_deg']:.2f} deg, stabilator {t['stabilator_deg']:.2f} deg, "
          f"throttle {t['throttle']:.3f}, L/D {t['lift_to_drag']:.1f}, static margin {par['design']['static_margin_from_tables']:.3f}, residual {t['residual_max_abs']:.1e}")
    print(f"  limiter {L['alpha_limiter_deg']:.2f} deg, trimmed CL there {L['cl_trimmed_at_limiter']:.3f}, load factor there {L['load_factor_at_limiter_at_entry_speed']:.2f} g")
    print(f'  wrote {out}')


if __name__ == '__main__':
    main()
