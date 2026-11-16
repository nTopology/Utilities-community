"""Landing gear of the Fury model: a tricycle gear shown down, its bays and its doors.

  Landing gear legs        shock struts, braces, torque links, axles, brakes, landing light housings
  Landing gear pistons     the polished sliding tubes of the three shock struts
  Wheels, Tyres            two main wheels and one nose wheel
  Landing gear doors       two nose doors and two doors for each main bay, hanging open
  Landing lights           one lamp on each outer main door
  Bays                     cut into the outer mold line under the inlet duct

Layout read from the photographs (reference/PROPORTIONS.md, "Landing gear"):
  * the nose leg stands at the front of its bay, with a fork on one side of the wheel and torque links behind it;
  * each main leg leaves the lower corner of the fuselage and leans outboard, the wheel is outboard of the leg,
    a folding strut runs forward and up into the bay and a side brace runs inboard to the keel;
  * each main bay has an inner door hinged near the keel and an outer door hinged on the slanted lower side of the
    fuselage; they hang down in front of the leg, the outer door carries the landing light, the door edges are sawtooth.

Every point is a formula of the inputs in "06 Inputs | Landing gear" and of the fuselage size, so the gear moves
and stretches with them. The gear is drawn down. The input "Landing gear" set to 0 removes it and closes the bays
(the same large-offset switch as the tail type). How the gear folds into the bays is not modelled.
"""
from __future__ import annotations

import math

import fieldlab as fl
from fieldlab import X, Y, Z, absf, clamp, fmax, fmin, length2, length3
from shapes import rrect2
from oml import AY, BIG, BELLY, LREF

S_GEAR = '32 Landing gear'
IN = 0.0254

# bay outlines, inches at the reference size, measured from the axle stations
NOSE_BAY = dict(front=-9.0, aft=38.0, inner=0.0, outer=6.5, top=-10.5)       # two doors, hinged on the outer edges
MAIN_BAY = dict(front=-59.0, aft=7.0, inner=5.0, outer=19.0, top=-3.0)       # two doors, hinged on the inner and the outer edge
MAIN_DOOR_END = -18.0        # the main doors stop here; the leg stands in the open rest of the bay
OUTER_DOOR_RISE = 3.0        # the outer hinge of a main bay is this far above the belly line, on the slanted side [in]
SAWTOOTH = 4.0               # depth of the sawtooth door edges [in]
DOOR_THICKNESS = 0.6         # [in]
NOSE_DOOR_SPLAY, MAIN_DOOR_SPLAY, OUTER_DOOR_SPLAY = 15.0, 28.0, 20.0     # how far the open doors lean outboard of vertical [deg]
BAY_ROOF = 0.020             # wall left between a bay and the inlet duct [m]


# ---------------------------------------------------------------------------------------------- small shapes
def lerp(p, q, t):
    """The point a fraction t of the way from p to q."""
    return tuple(a + (b - a) * t for a, b in zip(p, q))


def shift(p, dx=0.0, dy=0.0, dz=0.0):
    return (p[0] + dx, p[1] + dy, p[2] + dz)


def rod(p, q, r, c):
    """Round rod from p to q with radius r, in the coordinates c. The end points may be formulas of the inputs."""
    ax, ay, az = c[0] - p[0], c[1] - p[1], c[2] - p[2]
    bx, by, bz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
    along = clamp((ax * bx + ay * by + az * bz) / (bx * bx + by * by + bz * bz), 0.0, 1.0)
    return length3(ax - bx * along, ay - by * along, az - bz * along) - r


def ball(p, r, c):
    return length3(c[0] - p[0], c[1] - p[1], c[2] - p[2]) - r


def disc(centre, radius, half, c):
    """Short cylinder with its axis across the aircraft."""
    return fmax(length2(c[0] - centre[0], c[2] - centre[2]) - radius, absf(c[1] - centre[1]) - half)


def lamp(centre, radius, half, c):
    """Short cylinder with its axis along the aircraft."""
    return fmax(length2(c[1] - centre[1], c[2] - centre[2]) - radius, absf(c[0] - centre[0]) - half)


def wheel(centre, R, width, c, holes):
    """(tyre, rim) of a wheel whose axle runs across the aircraft."""
    dx, dz = c[0] - centre[0], c[2] - centre[2]
    r, a = length2(dx, dz), absf(c[1] - centre[1])
    r_rim = R * 0.56
    tyre = fmax(rrect2(r, a, R, width * 0.5, width * 0.36), r_rim - r)
    flange = width * 0.36
    # half width of the rim against radius: wide at the flange, a thin web, a thick hub
    half = fmax(flange - (r_rim - r) * 2.2, flange * 0.35, fmin(flange * 0.75 - (r - r_rim * 0.30) * 2.5, flange * 0.95))
    rim = fmax(r - r_rim * 1.02, a - half)
    if holes:
        # eight lightening holes: two unique ones, repeated by the mirror planes through the axle
        ring = r_rim * 0.63
        cut = fmin(*[length2(absf(dx) - ring * math.cos(math.radians(k)), absf(dz) - ring * math.sin(math.radians(k))) - r_rim * 0.115
                     for k in (22.5, 67.5)])
        rim = fmax(rim, -cut)
    return tyre, rim


# ---------------------------------------------------------------------------------------------- the gear
class Gear:
    def __init__(self, model):
        self.model = model
        d, af = model.d, model.af
        self.d, self.af = d, af
        self.s = af.scale
        self.ws = (af.scale * d.raw('width_scale')).named('Breadth scale of the gear attachments', S_GEAR)
        self.hs = (af.scale * d.raw('height_scale')).named('Height scale of the gear attachments', S_GEAR)
        self.off = ((1.0 - d.raw('gear_down')) * BIG).named('Landing gear removed when > 0', S_GEAR)
        self.zg = (d.m('ground_line') * -1.0).named('Ground height [m]', S_GEAR)
        self.xn, self.xm = d.station('nose_gear_station'), d.station('main_gear_station')
        self.Rn = (d.m('nose_tyre_diameter') * 0.5).named('Nose tyre radius [m]', S_GEAR)
        self.Rm = (d.m('main_tyre_diameter') * 0.5).named('Main tyre radius [m]', S_GEAR)
        self.wn = (self.Rn * 0.68).named('Nose tyre width [m]', S_GEAR)
        self.wm = (self.Rm * 0.64).named('Main tyre width [m]', S_GEAR)
        self.yw = (d.m('gear_track') * 0.5).named('Main wheel centre from the centreline [m]', S_GEAR)
        self.belly_z = (BELLY(af.xr) * self.hs).named('Belly height at this station [m]', S_GEAR)
        self._memo = {}

    def _once(self, key, make):
        if key not in self._memo:
            self._memo[key] = make()
        return self._memo[key]

    # ------------------------------------------------------------------ points
    def main_points(self):
        """Pivot in the bay, wheel centre, and the foot of the leg (inboard of the wheel)."""
        zw = (self.zg + self.Rm).named('Main axle height [m]', S_GEAR)
        pivot = (self.xm, self.ws * (17.3 * IN), self.hs * (-11.5 * IN))
        centre = (self.xm, self.yw, zw)
        foot = (self.xm, self.yw - self.wm * 0.5 - 2.6 * IN, zw)
        return pivot, centre, foot

    def nose_points(self):
        """Top of the leg in the bay, wheel centre, and the fork crown above the tyre."""
        zw = (self.zg + self.Rn).named('Nose axle height [m]', S_GEAR)
        top = (self.xn, 0.0, self.hs * (-15.6 * IN))
        centre = (self.xn, 0.0, zw)
        crown = (self.xn, 0.0, zw + self.Rn + 2.4 * IN)
        return top, centre, crown

    # ------------------------------------------------------------------ main gear (built on |Y|: both sides at once)
    def main_parts(self):
        def make():
            c = (X, AY, Z)
            P, W, B = self.main_points()
            knee = lerp(P, B, 0.56)
            barrel = fmin(rod(P, knee, 1.7 * IN, c), rod(lerp(P, B, 0.52), knee, 2.05 * IN, c))
            trunnion = rod(shift(P, dx=self.s * (-5.0 * IN)), shift(P, dx=self.s * (9.0 * IN)), 1.25 * IN, c)
            piston = rod(knee, B, 1.15 * IN, c)
            fitting = ball(B, 1.9 * IN, c)
            axle = rod(B, shift(W, dy=self.wm * 0.5 + 0.5 * IN), 0.95 * IN, c)
            brake = disc(shift(W, dy=-(self.wm * 0.5 + 0.9 * IN)), self.Rm * 0.40, 0.75 * IN, c)
            # folding strut forward and up into the bay, with its knuckle half way
            low = lerp(P, B, 0.84)
            high = (self.xm - self.s * (28.0 * IN), self.ws * (11.0 * IN), self.hs * (-7.0 * IN))
            mid = lerp(low, high, 0.5)
            strut = fmin(rod(low, mid, 1.0 * IN, c), rod(mid, high, 0.85 * IN, c), ball(mid, 1.45 * IN, c), ball(low, 1.5 * IN, c))
            # side brace inboard to the keel
            brace = rod(lerp(P, B, 0.48), (self.xm, self.ws * (4.0 * IN), self.hs * (-14.5 * IN)), 0.8 * IN, c)
            # torque links behind the leg
            apex = shift(lerp(P, B, 0.76), dx=5.5 * IN)
            links = fmin(rod(shift(knee, dx=1.2 * IN), apex, 0.5 * IN, c), rod(apex, shift(lerp(P, B, 0.95), dx=1.0 * IN), 0.5 * IN, c))
            # landing light on the inside of the outer door, at its front edge
            sn, cs = math.sin(math.radians(OUTER_DOOR_SPLAY)), math.cos(math.radians(OUTER_DOOR_SPLAY))
            at = (self.xm + self.s * ((MAIN_BAY['front'] + SAWTOOTH + 3.4) * IN), self.ws * (MAIN_BAY['outer'] * IN) + 4.6 * IN * sn - 1.9 * IN * cs,
                  self.hs * (float(BELLY.value(0.49 * LREF)) + OUTER_DOOR_RISE * IN) - 4.6 * IN * cs - 1.9 * IN * sn)
            housing = lamp(at, 2.5 * IN, 1.5 * IN, c)
            lens = lamp(shift(at, dx=-1.6 * IN), 2.2 * IN, 0.25 * IN, c)
            legs = fmin(barrel, trunnion, fitting, axle, brake, strut, brace, links, housing).named('Main gear legs', S_GEAR)
            tyre, rim = wheel(W, self.Rm, self.wm, c, holes=True)
            return dict(legs=legs, piston=piston.named('Main gear pistons', S_GEAR), tyre=tyre.named('Main tyres', S_GEAR),
                        rim=rim.named('Main wheels', S_GEAR), lens=lens.named('Landing light lenses', S_GEAR))
        return self._once('main', make)

    # ------------------------------------------------------------------ nose gear
    def nose_parts(self):
        def make():
            c = (X, Y, Z)
            P, W, C = self.nose_points()
            knee = lerp(P, C, 0.55)
            barrel = fmin(rod(P, knee, 1.5 * IN, c), rod(lerp(P, C, 0.50), knee, 1.85 * IN, c))
            piston = rod(knee, C, 1.0 * IN, c)
            # fork on the right side of the wheel only
            yf = self.wn * 0.5 + 1.3 * IN
            elbow = (self.xn, yf, C[2] - 1.2 * IN)
            fork = fmin(ball(C, 1.6 * IN, c), rod(C, elbow, 1.05 * IN, c), rod(elbow, (self.xn, yf, W[2]), 0.95 * IN, c))
            axle = rod((self.xn, yf + 0.4 * IN, W[2]), (self.xn, self.wn * -0.5 - 0.4 * IN, W[2]), 0.8 * IN, c)
            apex = shift(lerp(P, C, 0.78), dx=5.0 * IN)
            links = fmin(rod(shift(knee, dx=1.0 * IN), apex, 0.45 * IN, c), rod(apex, shift(C, dx=1.0 * IN, dz=0.8 * IN), 0.45 * IN, c))
            # drag brace aft and up to the bay roof
            brace = rod(lerp(P, C, 0.42), (self.xn + self.s * (17.0 * IN), 0.0, self.hs * (-15.4 * IN)), 0.75 * IN, c)
            legs = fmin(barrel, fork, axle, links, brace).named('Nose gear leg', S_GEAR)
            tyre, rim = wheel(W, self.Rn, self.wn, c, holes=False)
            return dict(legs=legs, piston=piston.named('Nose gear piston', S_GEAR), tyre=tyre.named('Nose tyre', S_GEAR),
                        rim=rim.named('Nose wheel', S_GEAR))
        return self._once('nose', make)

    # ------------------------------------------------------------------ bays and doors
    def _sawtooth(self, across, width):
        """1 at the two edges of a door, 0 half way across it."""
        return absf(across * (2.0 / width) - 1.0)

    def _plan(self, bay, x_axle, two_doors, aft_teeth):
        """Outline of a bay in plan view (negative inside), with sawtooth front (and aft) edges: one tooth for each door."""
        y0, y1 = self.ws * (bay['inner'] * IN), self.ws * (bay['outer'] * IN)
        if two_doors:
            across, width = absf(AY - (y0 + y1) * 0.5), (y1 - y0) * 0.5
        else:
            across, width = y1 - AY, y1 - y0
        teeth = self._sawtooth(across, width) * (self.s * (SAWTOOTH * IN))
        front = x_axle + self.s * (bay['front'] * IN) + teeth
        aft = x_axle + self.s * (bay['aft'] * IN) - (teeth if aft_teeth else 0.0)
        return fmax(front - X, X - aft, AY - y1, y0 - AY)

    def nose_plan(self):
        return self._once('nose_plan', lambda: self._plan(NOSE_BAY, self.xn, False, True).named('Nose gear bay outline', S_GEAR))

    def main_plan(self):
        return self._once('main_plan', lambda: self._plan(MAIN_BAY, self.xm, True, False).named('Main gear bay outline', S_GEAR))

    def outlines(self):
        """The two bay outlines as one plan pattern (for the panel lines)."""
        return fmin(self.nose_plan(), self.main_plan()).named('Landing gear bay outlines', S_GEAR)

    def bay_space(self):
        """The bays: inside their plan outline, below their roof height, and a wall away from the inlet duct."""
        def make():
            roof = BAY_ROOF - self.af.duct_air()
            nose = fmax(self.nose_plan(), roof, Z - self.hs * (NOSE_BAY['top'] * IN)).named('Nose gear bay', S_GEAR)
            main = fmax(self.main_plan(), roof, Z - self.hs * (MAIN_BAY['top'] * IN)).named('Main gear bays', S_GEAR)
            return fmin(nose, main).named('Landing gear bay space', S_GEAR)
        return self._once('bay_space', make)

    def bays(self):
        """The bays as they are cut from the outer mold line: only with the gear down."""
        return (self.bay_space() + self.off).named('Landing gear bays (open)', S_GEAR)

    def _door(self, bay, x_axle, hinge_outer, splay, x_end=None, aft_teeth=True, share=0.5, rise=0.0):
        """A flat door hanging from its hinge line on the belly, leaning outboard by the splay angle.
        share: the part of the bay breadth this door covers. rise: hinge height above the belly line [in]."""
        y0, y1 = self.ws * (bay['inner'] * IN), self.ws * (bay['outer'] * IN)
        width = (y1 - y0) * share
        hinge = y1 if hinge_outer else y0
        sn, cs = math.sin(math.radians(splay)), math.cos(math.radians(splay))
        dy, dz = AY - hinge, Z - self.belly_z - self.hs * (rise * IN)
        down = dy * sn - dz * cs                                   # distance from the hinge across the door
        normal = dy * cs + dz * sn
        teeth = self._sawtooth(down, width) * (self.s * (SAWTOOTH * IN))
        front = x_axle + self.s * (bay['front'] * IN) + teeth
        aft = x_axle + self.s * ((bay['aft'] if x_end is None else x_end) * IN) - (teeth if aft_teeth else 0.0)
        return fmax(absf(normal) - DOOR_THICKNESS * IN * 0.5, -down, down - width, front - X, X - aft)

    def doors(self):
        def make():
            nose = self._door(NOSE_BAY, self.xn, True, NOSE_DOOR_SPLAY, share=1.0).named('Nose gear doors', S_GEAR)
            inner = self._door(MAIN_BAY, self.xm, False, MAIN_DOOR_SPLAY, x_end=MAIN_DOOR_END, aft_teeth=False)
            outer = self._door(MAIN_BAY, self.xm, True, OUTER_DOOR_SPLAY, x_end=MAIN_DOOR_END - 4.0, aft_teeth=False, share=0.8, rise=OUTER_DOOR_RISE)
            return fmin(nose, inner.named('Main gear inner doors', S_GEAR), outer.named('Main gear outer doors', S_GEAR))
        return self._once('doors', make)

    # ------------------------------------------------------------------ bodies
    def bodies(self):
        """(name, field, material, mesh size) of the gear bodies."""
        m, n = self.main_parts(), self.nose_parts()
        off = self.off
        return [('Landing gear legs', (fmin(m['legs'], n['legs']) + off).named('Landing gear legs', S_GEAR), 'gear_paint', 0.0025),
                ('Landing gear pistons', (fmin(m['piston'], n['piston']) + off).named('Landing gear pistons', S_GEAR), 'hyd', 0.0025),
                ('Wheels', (fmin(m['rim'], n['rim']) + off).named('Wheels', S_GEAR), 'alu', 0.0025),
                ('Tyres', (fmin(m['tyre'], n['tyre']) + off).named('Tyres', S_GEAR), 'rubber', 0.003),
                ('Landing gear doors', (self.doors() + off).named('Landing gear doors', S_GEAR), 'door', 0.003),
                ('Landing lights', (m['lens'] + off).named('Landing lights', S_GEAR), 'lens_clear', 0.002)]

    def box(self):
        d = self.d
        L = d.value('length') * 0.3048
        half = d.value('gear_track') * 0.0254 * 0.5 + 0.25
        return ([d.value('nose_gear_station') * 0.01 * L - 0.9, -half, -d.value('ground_line') * 0.0254 - 0.03],
                [d.value('main_gear_station') * 0.01 * L + 0.6, half, -0.03 * L * 0.0 - 0.05])
