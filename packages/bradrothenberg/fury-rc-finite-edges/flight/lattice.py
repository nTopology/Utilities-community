"""Vortex-lattice derivatives of the Fury (conventional tail) for the flight model: lift, pitch, lateral, damping and
control derivatives, with Mach number by the Prandtl-Glauert rule.

Uses the lattice of analysis/vlm.py (wing and horizontal tail carried to the centreline, fin; flat surfaces from the
planform inputs) and adds what a flight model needs: any onset flow (angle of attack, sideslip, roll, pitch and yaw
rate), control deflections as a change of the boundary condition on the panels of the surface, and forces from the local
onset velocity on each bound vortex, so terms that grow with lift (roll due to sideslip of a swept wing, yaw due to
roll rate) appear.

Estimate. No fuselage, no thickness, no camber, no viscosity, rigid wake straight aft. Model frame: x aft, y to
starboard, z up. Results are in the body-axis sign convention (x forward, y right, z down): Cl positive right wing
down, Cm positive nose up, Cn positive nose right; beta positive = wind from the right; rates non-dimensional
p b / 2V, q c / 2V, r b / 2V; deflections in radians, measured in the stream direction times cos(hinge sweep):
  elevator  both horizontal tail panels as one all-moving surface, positive trailing edge down
  flap      both flaperons together, positive trailing edge down
  aileron   flaperons against each other: +1 = left trailing edge down by 1 rad, right up by 1 rad (rolls right)
  rudder    positive trailing edge to the left (nose left)
"""
from __future__ import annotations
import math
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
sys.path.insert(0, str(ROOT / 'model'))
import vlm as base  # noqa: E402

NC, NS = 8, 24
FLAPERON = dict(eta_in=0.27, eta_out=0.80, chord_fraction_aft=0.25)     # model/aircraft.py control-surface gaps: hinge at 76 % chord, 27 to 80 % of the half span
RUDDER = dict(eta_in=0.10, eta_out=0.93, chord_fraction_aft=0.375)     # hinge at 66 % chord (lattice: the last three of eight panels), 10 to 93 % of the fin height
XHAT = np.array([1.0, 0.0, 0.0])


def _index(mirror):
    """(strip, chordwise panel, side) of every panel in the order analysis/vlm.py panel() writes them. side: +1 starboard, -1 port."""
    th = np.linspace(0.0, math.pi / 2, NS + 1)
    eta = np.sin(th)
    mid = 0.5 * (eta[:-1] + eta[1:])
    rows = []
    for i in range(NS):
        for j in range(NC):
            rows.append((mid[i], (j + 0.5) / NC, 1.0))
            if mirror:
                rows.append((mid[i], (j + 0.5) / NC, -1.0))
    return np.array(rows)


class Lattice:
    def __init__(self, d, mach=0.0, x_ref=None, tail=True):
        self.ref = base.reference(d)
        parts = base.surfaces(d, 'conventional' if tail else 'none')
        self.names = [p[0] for p in parts]
        self.A = np.vstack([p[1][0] for p in parts])
        self.B = np.vstack([p[1][1] for p in parts])
        self.P = np.vstack([p[1][2] for p in parts])
        self.owner = np.concatenate([[k] * len(p[1][0]) for k, p in enumerate(parts)])
        self.idx = np.vstack([_index(name != 'fin') for name in self.names])
        self.mach = mach
        bt = math.sqrt(1.0 - mach * mach)
        s = np.array([1.0 / bt, 1.0, 1.0])              # Prandtl-Glauert: the lattice is solved on the geometry stretched in x by 1 / beta,
        As, Bs, Ps = self.A * s, self.B * s, self.P * s  # with the true boundary condition and the true bound vectors in the forces
        self.L = self.B - self.A
        n = np.cross(XHAT[None], self.L)
        self.N = n / np.linalg.norm(n, axis=1)[:, None]
        self.M = np.einsum('ijk,ik->ij', base.horseshoe(Ps, As, Bs), self.N)
        self.Minv = np.linalg.inv(self.M)
        self.mid = 0.5 * (self.A + self.B)
        self.x_ref = np.array([self.ref['x_mac_le'] + 0.25 * self.ref['mac'] if x_ref is None else x_ref, 0.0, 0.0])
        v = d.value
        self.cos_hinge = dict(
            flap=math.cos(math.atan(math.tan(math.radians(v('wing_sweep'))) - 0.75 * (v('wing_root_chord') - v('wing_tip_chord')) / (v('wing_span') / 2))),
            rudder=math.cos(math.atan(math.tan(math.radians(v('fin_sweep'))) - 0.625 * (v('fin_root_chord') - v('fin_tip_chord')) / v('fin_height'))),
            elevator=1.0)
        own = lambda name: self.owner == self.names.index(name) if name in self.names else np.zeros(len(self.owner), bool)
        eta, xc, side = self.idx[:, 0], self.idx[:, 1], self.idx[:, 2]
        fl = own('wing') & (eta > FLAPERON['eta_in']) & (eta < FLAPERON['eta_out']) & (xc > 1.0 - FLAPERON['chord_fraction_aft'])
        self.mask = dict(flap_left=fl & (side < 0), flap_right=fl & (side > 0), elevator=own('horizontal tail'),
                         rudder=own('fin') & (eta > RUDDER['eta_in']) & (eta < RUDDER['eta_out']) & (xc > 1.0 - RUDDER['chord_fraction_aft']))

    def solve(self, alpha=0.0, beta=0.0, ph=0.0, qh=0.0, rh=0.0, elevator=0.0, flap=0.0, aileron=0.0, rudder=0.0):
        """Coefficients dict(CL, CY, Cl, Cm, Cn, CX) for unit speed. Small-angle onset flow (1, -beta, alpha) plus the rotation."""
        r = self.ref
        om = np.array([-ph * 2.0 / r['b'], qh * 2.0 / r['mac'], -rh * 2.0 / r['b']])       # body rates (p, q, r) as a vector in the model frame
        onset = lambda pts: np.array([1.0, -beta, alpha])[None] - np.cross(om[None], pts - self.x_ref[None])
        rhs = -np.einsum('ij,ij->i', self.N, onset(self.P))
        # a deflected surface: the panel normal turns, which acts like a local change of the onset flow normal to the panel
        rhs = rhs - self.mask['elevator'] * elevator * self.cos_hinge['elevator']
        rhs = rhs - (self.mask['flap_left'] * (flap + aileron) + self.mask['flap_right'] * (flap - aileron)) * self.cos_hinge['flap']
        rhs = rhs + self.mask['rudder'] * rudder * self.cos_hinge['rudder']
        gam = self.Minv @ rhs
        F = gam[:, None] * np.cross(onset(self.mid), self.L)                  # rho = 1
        mom = np.cross(self.mid - self.x_ref[None], F).sum(0)
        f = F.sum(0)
        qs = 0.5 * r['S']
        return dict(CL=f[2] / qs, CY=f[1] / qs, CX=-f[0] / qs, Cl=-mom[0] / (qs * r['b']), Cm=mom[1] / (qs * r['mac']), Cn=-mom[2] / (qs * r['b']),
                    share={n: float(F[self.owner == k, 2].sum() / qs) for k, n in enumerate(self.names)})

    def derivatives(self, alpha0=0.0):
        """Central differences about an angle of attack. Returns {coefficient: {variable: slope}}."""
        steps = dict(alpha=0.01, beta=0.01, ph=0.005, qh=0.002, rh=0.005, elevator=0.01, flap=0.01, aileron=0.01, rudder=0.01)
        out = {}
        for var, h in steps.items():
            a = self.solve(**{'alpha': alpha0, **({var: h} if var != 'alpha' else {'alpha': alpha0 + h})})
            b = self.solve(**{'alpha': alpha0, **({var: -h} if var != 'alpha' else {'alpha': alpha0 - h})})
            for c in ('CL', 'CY', 'Cl', 'Cm', 'Cn'):
                out.setdefault(c, {})[var] = (a[c] - b[c]) / (2 * h)
        out['CL0'] = self.solve(alpha=alpha0)['CL']
        return out


def helmbold(ar, sweep_half_deg, mach):
    b2 = 1.0 - mach * mach
    return 2 * math.pi * ar / (2 + math.sqrt(4 + ar * ar * (b2 + math.tan(math.radians(sweep_half_deg)) ** 2)))


def check():
    """Wing alone against the Helmbold/DATCOM formula, and the sign of every control derivative."""
    from design import Design
    d = Design()
    v = d.value
    r = base.reference(d)
    ar = r['b'] ** 2 / r['S']
    half = math.degrees(math.atan(math.tan(math.radians(v('wing_sweep'))) - 0.5 * (v('wing_root_chord') - v('wing_tip_chord')) / (v('wing_span') / 2)))
    rows = []
    for m in (0.0, 0.6, 0.8):
        lat = Lattice(d, m, tail=False)
        cla = lat.derivatives()['CL']['alpha']
        rows.append(dict(mach=m, lattice_cl_alpha=cla, helmbold_cl_alpha=helmbold(ar, half, m), ratio=cla / helmbold(ar, half, m)))
    lat = Lattice(d, 0.0)
    dv = lat.derivatives()
    signs = dict(elevator_down_gives_lift=dv['CL']['elevator'] > 0, elevator_down_pitches_nose_down=dv['Cm']['elevator'] < 0,
                 flap_down_gives_lift=dv['CL']['flap'] > 0, aileron_rolls_right=dv['Cl']['aileron'] > 0,
                 rudder_left_yaws_left=dv['Cn']['rudder'] < 0, rudder_left_pushes_right=dv['CY']['rudder'] > 0,
                 roll_damping=dv['Cl']['ph'] < 0, pitch_damping=dv['Cm']['qh'] < 0, yaw_damping=dv['Cn']['rh'] < 0,
                 weathercock_stable=dv['Cn']['beta'] > 0, side_force_opposes_sideslip=dv['CY']['beta'] < 0)
    signs = {k: bool(x) for k, x in signs.items()}
    return dict(aspect_ratio=ar, half_chord_sweep_deg=half, wing_alone=rows, signs=signs, all_signs_ok=all(signs.values()))


if __name__ == '__main__':
    import json
    c = check()
    print(json.dumps(c, indent=1))
    from design import Design
    for m in (0.0, 0.5):
        lat = Lattice(Design(), m)
        for a0 in (0.0, 0.1):
            dv = lat.derivatives(a0)
            print('Mach %.1f alpha0 %.2f CL0 %.3f' % (m, a0, dv['CL0']))
            for c_ in ('CL', 'CY', 'Cl', 'Cm', 'Cn'):
                print('  ', c_, {k: round(x, 4) for k, x in dv[c_].items()})
