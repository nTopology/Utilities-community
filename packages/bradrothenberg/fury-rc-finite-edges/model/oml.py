"""Fury outer mold line as native Spline DF lofts (metres, negative inside).

Frame: X aft from the nose tip, Y to starboard, Z up from the fuselage reference line (the chine line
of the forebody, which is also the wing chord plane).

How the shape is built (the same technique as the X-47B model):

  A loft is one planar Spline DF section whose control points move along the aircraft on fair guide
  curves. The fuselage uses four lofts, all drawn in the cross-section plane (half breadth, height):

      Fuselage upper section      crown to chine                 solid below the curve
      Underside and duct roof     chine to keel, then duct roof  solid above the curve
      Lower fuselage section      chine to the cowl bottom       solid above the curve
      Duct floor section          duct edge to the duct bottom   air above the curve

  The body is where "below the upper curve" and "above a lower curve" overlap. The inlet is not drawn
  as an opening: the lower fuselage is cut by a raked plane (the lip plane), and the air path, which is
  "below the roof, above the floor, inside the cowl skin", is removed from it.

  Wing and tails are lifting panels: one airfoil half-thickness curve in the (station, distance from the
  chord plane) plane, with the leading edge, chord and thickness given along the panel by straight lines.

  The fuselage is drawn at the size of the reference aircraft (LREF metres long) in "reference
  coordinates"; the three fuselage inputs (length, width scale, height scale) stretch those coordinates.

Source tags in the comments:
  [SIDE]  side-view photographs    [PLAN] underside photographs    [FRONT] head-on photographs
  see reference/PROPORTIONS.md and docs/MATCH.md
"""
from __future__ import annotations

import math

import numpy as np

import fieldlab as fl
from fieldlab import X, Y, Z, absf, clamp, const, fmax, fmin, lift, sminq, smax, spline2d
from shapes import G
from regions import interp_ctrl
from design import Design, S_DIM

AY = absf(Y)

S_COORD = '07 Reference coordinates'
S_GUIDE = '10 Fuselage guide curves'
S_FUS = '11 Fuselage lofts'
S_DUCT = '12 Inlet, duct and nozzle'
S_ASM = '13 Fuselage'
S_WING = '14 Wing'
S_TAIL = '15 Tail'
S_EXT = '16 Exterior'

# --------------------------------------------------------------------------
# reference aircraft
# --------------------------------------------------------------------------
LREF = 10.2108               # fuselage length of the reference aircraft, nose tip to nozzle exit (m) = 33.5 ft

# stations and sizes of the propulsion path, as fractions of the fuselage length
T_LIP = 0.292                # lower inlet lip [SIDE]
T_ROOF_FREE = 0.385          # up to here the duct roof is the forebody underside itself
T_FACE = 0.745               # engine (compressor) face
T_DROP = (0.40, 0.52)        # the duct roof is one diverter height + plate thickness below the underside loft up to the first station, and on it from the second
T_ENGINE_REAR = T_FACE + 1.742 / LREF   # engine exhaust flange: one engine length (1.742 m) aft of the face
Z_ENGINE = 0.0340            # engine axis height / length [SIDE: centre of the tail fairing]
R_FACE = 0.293 / LREF       # duct radius at the engine face / length (the engine inlet radius, 0.293 m)


def _g(name, ts, vs, scale=LREF, section=S_GUIDE):
    """Guide along the reference station. ts are fractions of the length, vs fractions of the length
    (scale = LREF) or plain numbers (scale = 1)."""
    g = G(name, [t * LREF for t in ts], [v * scale for v in vs])
    g.section = section
    return g


# -- fuselage outline -------------------------------------------------------------------------------
_T = [0.0, 0.03, 0.06, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0]

HALF_WIDTH = _g('Fuselage half width', _T,                                   # [PLAN], chine line
                [0.0008, 0.0105, 0.0200, 0.0315, 0.0445, 0.0560, 0.0660, 0.0720, 0.0755, 0.0775, 0.0785, 0.0790,
                 0.0790, 0.0788, 0.0780, 0.0765, 0.0735, 0.0690, 0.0635, 0.0555, 0.0450, 0.0340])
CROWN = _g('Crown height', _T,                                               # [SIDE] upper outline of photograph 07
           [0.0015, 0.0160, 0.0280, 0.0415, 0.0530, 0.0622, 0.0662, 0.0702, 0.0728, 0.0746, 0.0760, 0.0770,
            0.0775, 0.0777, 0.0773, 0.0760, 0.0738, 0.0706, 0.0672, 0.0642, 0.0618, 0.0600])
CHINE = _g('Chine height', [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 0.60, 0.68, 0.76, 0.84, 0.92, 1.0],   # height of the widest point [SIDE]
           [0.0, 0.0030, 0.0055, 0.0075, 0.0090, 0.0100, 0.0100, 0.0100, 0.0110, 0.0150, 0.0215, 0.0290, 0.0340])
UPPER_ROUND = _g('Upper section roundness', [0.0, 0.50, 0.62, 0.74, 0.86, 0.95, 1.0],      # [FRONT] the arch stays an arch over the wing
                 [0.0, 0.0, 0.12, 0.38, 0.75, 1.0, 1.0], scale=1.0)

# -- underside of the forebody, continued aft as the roof of the inlet duct ---------------------------
_TU = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.345, T_ROOF_FREE, 0.43, 0.48, 0.54, 0.60, 0.66, 0.71, T_FACE, 1.0]
ROOF = _g('Underside and duct roof height', _TU,                             # [SIDE] keel, then S-duct roof
          [-0.0004, -0.0070, -0.0085, -0.0085, -0.0072, -0.0062, -0.0058, -0.0056, -0.0045, -0.0010, 0.0080,
           0.0240, 0.0410, 0.0540, 0.0605, Z_ENGINE + R_FACE, Z_ENGINE + R_FACE])
_ER = Z_ENGINE * LREF - CHINE.value(T_FACE * LREF)             # the duct edge ends on the engine axis
EDGE_RISE = _g('Duct edge rise above the chine', [0.0, T_ROOF_FREE, 0.43, 0.50, 0.58, 0.66, 0.71, T_FACE, 1.0],
               [0.0, 0.0, 0.0004, 0.0040, 0.0110, 0.0180, 0.0200, _ER / LREF, _ER / LREF])
_RW = R_FACE * LREF / HALF_WIDTH.value(T_FACE * LREF)        # the duct is as wide as the engine face there
ROOF_WIDTH = _g('Duct width ratio', [0.0, T_ROOF_FREE, 0.43, 0.48, 0.54, 0.60, 0.66, 0.71, T_FACE, 1.0],
                [1.0, 1.0, 0.86, 0.74, 0.62, 0.52, 0.44, 0.39, _RW, _RW], scale=1.0)
DUCT_ROUND = _g('Duct section roundness', [0.0, T_ROOF_FREE, 0.45, 0.55, 0.65, 0.71, T_FACE, 1.0],
                [0.0, 0.0, 0.18, 0.55, 0.88, 1.0, 1.0, 1.0], scale=1.0)
# floor heights found by tools/tune_duct.py: throat area = 0.84 x engine face area just behind the lower lip,
# growing smoothly to the engine face area (a gentle diffuser)
FLOOR = _g('Duct floor height', [0.26, T_LIP, 0.345, T_ROOF_FREE, 0.43, 0.48, 0.54, 0.60, 0.66, 0.71, T_FACE, 1.0],
           [-0.0323, -0.0365, -0.0335, -0.0317, -0.0300, -0.0217, -0.0093, 0.0009, 0.0055, 0.0059,
            Z_ENGINE - R_FACE, Z_ENGINE - R_FACE])

# -- lower fuselage: the inlet cowl, the belly and the tail cone [SIDE] --------------------------------
BELLY = _g('Lower fuselage height', [0.26, T_LIP, 0.345, 0.40, 0.50, 0.58, 0.66, 0.70, 0.74, 0.78, 0.82, 0.86, 0.90, 0.95, 1.0],
           [-0.0320, -0.0360, -0.0390, -0.0420, -0.0450, -0.0455, -0.0430, -0.0390, -0.0365, -0.0335, -0.0285,
            -0.0220, -0.0140, -0.0035, 0.0080])
LOWER_ROUND = _g('Lower section roundness', [0.26, 0.55, 0.66, 0.78, 0.90, 1.0], [0.0, 0.0, 0.15, 0.55, 1.0, 1.0], scale=1.0)

# -- jet pipe: a straight cone on the engine axis from the engine to the nozzle exit -----------------
R_PIPE = 0.170 / LREF       # jet pipe radius at the engine / length (the engine exhaust radius, 0.170 m)


# --------------------------------------------------------------------------
# unit section shapes (control nets, fitted once)
# --------------------------------------------------------------------------
def _net_out(p, n=7, straight_end=False):
    """Unit upper half section from the centre (0, 1) out to the edge (1, 0): v = (1 - eta^p)^(1/q).
    straight_end=False ends with a vertical leg (tangent to a round side)."""
    e = np.linspace(0, 1, 200)
    if straight_end:
        v = 1 - e ** p
    else:
        th = np.linspace(0, math.pi / 2, 200)
        e, v = np.sin(th) ** (2 / p), np.cos(th) ** (2 / p)
    c = interp_ctrl(np.c_[e, v], n)
    c[0], c[-1] = [0.0, 1.0], [1.0, 0.0]
    c[1][1] = 1.0                                   # level across the centreline
    if not straight_end:
        c[-2][0] = 1.0                              # vertical at the widest point
    return c


ARCH_NET = _net_out(1.75, straight_end=True)        # forebody: an arch that meets the chine at an angle
DOME_NET = _net_out(2.3)                            # aft body: round shoulders, vertical sides


def _net_in(pts, n=10, vertical_start=False):
    """Unit lower half section from the edge (1, 0) in to the centre (0, 1) (v is the depth fraction)."""
    c = interp_ctrl(np.asarray(pts, float), n)
    c[0], c[-1] = [1.0, 0.0], [0.0, 1.0]
    c[-2][1] = 1.0                                  # level across the centreline
    if vertical_start:
        c[1][0] = 1.0
    return c


_e = np.linspace(1, 0, 200)
LENS_NET = _net_in(np.c_[_e, 1 - _e ** 2])                                   # shallow keel of the forebody
_th = np.linspace(0, math.pi / 2, 200)
ROUND_NET = _net_in(np.c_[np.cos(_th), np.sin(_th)], vertical_start=True)    # quarter circle
# inlet cowl [FRONT]: a short ledge under the chine (the forebody overhangs the cowl), slanted side wall,
# rounded corner, nearly flat bottom
_ledge = np.c_[np.linspace(1.0, 0.87, 20), np.linspace(0.0, 0.05, 20)]
_wall = np.c_[np.linspace(0.87, 0.62, 60)[1:], np.linspace(0.05, 0.82, 60)[1:]]
_a = np.linspace(0, 1, 30)[1:]
_corner = np.c_[0.62 - 0.14 * _a, 0.82 + 0.12 * np.sin(_a * math.pi / 2)]
_bottom = np.c_[np.linspace(0.48, 0.0, 60)[1:], 0.94 + 0.06 * (1 - np.linspace(1, 0, 60)[1:] ** 2)]
TRAPEZOID_NET = _net_in(np.vstack([_ledge, _wall, _corner, _bottom]))


def thickness_coefficients(a0, um, te_slope=-0.9):
    """yt(u) = a0 sqrt(u) + a1 u + a2 u^2 + a3 u^3 + a4 u^4: half thickness per unit thickness,
    0.5 at u = um with zero slope there, zero at the trailing edge."""
    A = np.array([[um, um ** 2, um ** 3, um ** 4],
                  [1, 2 * um, 3 * um ** 2, 4 * um ** 3],
                  [1, 1, 1, 1],
                  [1, 2, 3, 4]], float)
    b = np.array([0.5 - a0 * math.sqrt(um), -0.5 * a0 / math.sqrt(um), -a0, te_slope - 0.5 * a0])
    return (a0,) + tuple(np.linalg.solve(A, b))


FOIL = thickness_coefficients(0.62, 0.42)           # thin section, maximum thickness at 42 % chord


def foil_half(u):
    u = np.clip(u, 0, 1)
    a0, a1, a2, a3, a4 = FOIL
    return a0 * np.sqrt(u) + u * (a1 + u * (a2 + u * (a3 + u * a4)))


def _foil_net(n=9):
    """Control net (u, t) of the unit half-thickness curve from the leading edge to the trailing edge.
    The first leg is vertical, so the two mirrored halves meet tangent at the nose."""
    from scipy.interpolate import BSpline
    u = 0.5 * (1 - np.cos(np.linspace(0, math.pi, 400)))
    pts = np.c_[u, foil_half(u)]
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    t = np.linspace(0, d[-1], 400)
    Q = np.c_[np.interp(t, d, pts[:, 0]), np.interp(t, d, pts[:, 1])]
    knots = np.r_[np.zeros(4), np.arange(1, n - 3) / (n - 3), np.ones(4)]
    A = BSpline.design_matrix(np.clip(t / d[-1], 0, 1 - 1e-12), knots, 3).toarray()
    c = np.zeros((n, 2))
    c[-1] = [1.0, 0.0]
    rhs = Q - np.outer(A[:, -1], c[-1])
    c[2:-1, 0] = np.linalg.lstsq(A[:, 2:-1], rhs[:, 0], rcond=None)[0]
    c[1:-1, 1] = np.linalg.lstsq(A[:, 1:-1], rhs[:, 1], rcond=None)[0]
    return c


FOIL_NET = _foil_net()
BIG = 100.0                  # offset that removes the tail set that is not selected


# --------------------------------------------------------------------------
# the airframe
# --------------------------------------------------------------------------
class Airframe:
    """All exterior fields for one set of design inputs."""

    def __init__(self, design: Design | None = None):
        d = self.d = design or Design()
        self.L = d.m('length')
        # reference coordinates: the fuselage is drawn LREF metres long and stretched by the inputs
        self.scale = (self.L / LREF).named('Length scale', S_DIM)
        self.xr = (X / self.scale).named('Reference station', S_COORD)
        self.yr = (AY / (self.scale * d.raw('width_scale'))).named('Reference half breadth', S_COORD)
        self.zr = (Z / (self.scale * d.raw('height_scale'))).named('Reference height', S_COORD)
        self._memo = {}
        self.panels = {}

    def _once(self, key, make):
        if key not in self._memo:
            self._memo[key] = make()
        return self._memo[key]

    # ------------------------------------------------------------------ fuselage lofts
    def _section(self, label, net, half, z_edge, z_centre, net2=None, weight=None):
        """Spline DF in the cross-section plane. A control point is (half * eta, z_edge + (z_centre - z_edge) * v);
        with a second net and a weight the shape changes along the loft."""
        cps = []
        for i in range(len(net)):
            e, v = float(net[i][0]), float(net[i][1])
            if net2 is not None:
                e = weight * float(net2[i][0] - net[i][0]) + e
                v = weight * float(net2[i][1] - net[i][1]) + v
            cps.append((half * e, z_edge + (z_centre - z_edge) * v))
        return spline2d(cps, self.yr, self.zr, label=label)

    def upper(self):
        """Solid below: crown to chine."""
        def make():
            x = self.xr
            f = self._section('Fuselage upper section', ARCH_NET, HALF_WIDTH(x), CHINE(x), CROWN(x), DOME_NET, UPPER_ROUND(x))
            return f.named('Fuselage upper loft', S_FUS)
        return self._once('upper', make)

    def duct_half_width(self):
        return (HALF_WIDTH(self.xr) * ROOF_WIDTH(self.xr)).named('Duct half width', S_FUS)

    def duct_edge(self):
        """Height of the side edge shared by the duct roof and the duct floor: the chine up to the inlet, the engine axis at the engine."""
        return (CHINE(self.xr) + EDGE_RISE(self.xr)).named('Duct edge height', S_FUS)

    def roof(self):
        """Solid above: the forebody underside, continued aft as the roof of the inlet duct."""
        def make():
            x = self.xr
            f = self._section('Underside and duct roof section', LENS_NET, self.duct_half_width(), self.duct_edge(), ROOF(x),
                              ROUND_NET, DUCT_ROUND(x))
            return f.named('Underside and duct roof loft', S_FUS)
        return self._once('roof', make)

    def belly(self):
        """Solid above: inlet cowl, belly and tail cone."""
        def make():
            x = self.xr
            f = self._section('Lower fuselage section', TRAPEZOID_NET, HALF_WIDTH(x), CHINE(x), BELLY(x), ROUND_NET, LOWER_ROUND(x))
            return f.named('Lower fuselage loft', S_FUS)
        return self._once('belly', make)

    def floor(self):
        """Air above: the floor and side walls of the inlet duct."""
        def make():
            x = self.xr
            f = self._section('Duct floor section', TRAPEZOID_NET, self.duct_half_width(), self.duct_edge(), FLOOR(x),
                              ROUND_NET, DUCT_ROUND(x))
            return f.named('Duct floor loft', S_DUCT)
        return self._once('floor', make)

    # ------------------------------------------------------------------ inlet
    def lip_plane(self):
        """Positive ahead of the inlet lip surface (reference coordinates). The lower lip is a chevron swept back from
        the centreline, and the side walls lean forward going up to the forebody underside [SIDE, photographs 07 and 18]."""
        def make():
            d = self.d
            x_lip = (d.raw('inlet_station') * (0.01 * LREF)).named('Inlet lip reference station', S_DIM)
            z_lip = BELLY.value(T_LIP * LREF)
            f = (x_lip + self.yr * d.tan('inlet_lip_sweep') - (self.zr - z_lip) * d.tan('inlet_rake') - self.xr) * d.cos('inlet_rake')
            return f.named('Inlet lip surface', S_DUCT)
        return self._once('lip', make)

    def lip_thickness(self):
        return (self.d.m('lip_thickness') / self.scale).named('Reference lip thickness', S_DIM)

    # ------------------------------------------------------------------ diverter and splitter plate
    def diverter_height(self):
        return (self.d.m('diverter_height') / self.scale).named('Reference diverter height', S_DIM)

    def splitter_thickness(self):
        return (self.d.m('splitter_thickness') / self.scale).named('Reference splitter plate thickness', S_DIM)

    def roof_drop(self):
        """How far the duct roof sits below the forebody underside: diverter height plus plate thickness at the inlet,
        fading to nothing further aft, where the duct roof is the underside loft itself."""
        def make():
            fade = 1.0 - fl.smoothstep(T_DROP[0] * LREF, T_DROP[1] * LREF, self.xr)
            return ((self.diverter_height() + self.splitter_thickness()) * fade).named('Duct roof drop below the underside loft', S_DUCT)
        return self._once('drop', make)

    def splitter_edge(self):
        """Positive ahead of the splitter plate leading edge: an arrowhead with its point on the centreline."""
        d = self.d
        x_apex = (d.raw('splitter_apex') * (0.01 * LREF)).named('Splitter plate apex reference station', S_DIM)
        return (x_apex + self.yr * d.tan('splitter_sweep') - self.xr).named('Splitter plate leading edge', S_DUCT)

    def splitter(self):
        """The splitter plate: the upper lip of the inlet. It lies one diverter height below the forebody underside,
        thins toward its leading edge, and ends at the sides in the cowl [photographs 07, 18, 19]."""
        def make():
            below = self.roof()                                   # distance below the forebody underside
            thick = clamp(-self.splitter_edge() * 0.18, self.splitter_thickness() * 0.4, self.splitter_thickness())
            top = self.diverter_height() + self.splitter_thickness() - thick
            f = fmax(top - below, below - self.diverter_height() - self.splitter_thickness(), self.splitter_edge(), self.belly(), self.xr - T_DROP[0] * LREF)
            return f.named('Splitter plate', S_DUCT)
        return self._once('splitter', make)

    def diverter_slot(self):
        """The diverter slot: the gap between the forebody underside and the splitter plate. Behind the inlet lip a swept
        wedge closes it, so the slot opens to the sides under the chine."""
        def make():
            d = self.d
            x_wedge = ((d.raw('inlet_station') + 0.5) * (0.01 * LREF)).named('Diverter wedge apex reference station', S_DIM)
            wedge = self.xr - x_wedge - self.yr * d.tan('diverter_sweep')
            f = fmax(-self.roof(), self.roof() - self.diverter_height(), wedge)
            return f.named('Diverter slot', S_DUCT)
        return self._once('slot', make)

    def duct_core(self):
        """Inlet duct air, not yet limited by the lip surface: below the roof, above the floor, inside the cowl skin,
        between the duct side edges. At the inlet the roof is the underside of the splitter plate."""
        def make():
            f = fmax(self.roof_drop() - self.roof(), self.floor(), self.belly() + self.lip_thickness(), self.yr - self.duct_half_width(), self.xr - T_FACE * LREF)
            return f.named('Inlet duct air (uncut)', S_DUCT)
        return self._once('duct_core', make)

    def lower(self, opened=True):
        """Solid above: forebody underside plus the lower fuselage aft of the lip plane (with or without the duct)."""
        def make():
            lip_radius = self.lip_thickness() * 1.2
            cowl = fmax(self.belly(), -self.duct_core()) if opened else self.belly()
            # the lip plane cuts the cowl only below the forebody underside; above it the body carries on
            cowl = smax_field(cowl, fmin(self.lip_plane(), self.roof()), lip_radius)
            # the splitter plate carries on ahead of the lip; the diverter slot separates it from the forebody
            cowl = fmax(fmin(cowl, self.splitter()), -self.diverter_slot())
            fore = fmax(self.roof(), self.xr - T_ROOF_FREE * LREF)
            return fmin(fore, cowl).named('Fuselage lower side' if opened else 'Fuselage lower side, inlet closed', S_ASM)
        return self._once(('lower', opened), make)

    # ------------------------------------------------------------------ nozzle
    def jet_pipe(self):
        """Air: straight cone on the engine axis from the engine to the nozzle exit (reference coordinates)."""
        def make():
            d = self.d
            r_exit = (d.m('nozzle_diameter') * 0.5 / self.scale).named('Reference nozzle exit radius', S_DIM)
            t = clamp((self.xr - T_ENGINE_REAR * LREF) / ((1.0 - T_ENGINE_REAR) * LREF), 0.0, 1.0)
            radius = (r_exit - R_PIPE * LREF) * t + R_PIPE * LREF
            f = fmax(fl.length2(self.yr, self.zr - Z_ENGINE * LREF) - radius, (T_ENGINE_REAR - 0.004) * LREF - self.xr)
            return f.named('Jet pipe air', S_DUCT)
        return self._once('jet', make)

    # ------------------------------------------------------------------ fuselage
    def fuselage(self, opened=True):
        """Fuselage in real coordinates. opened=False leaves the inlet and nozzle closed (for aerodynamics)."""
        def make():
            body = fmax(self.upper(), self.lower(opened), -self.xr, self.xr - LREF)
            if opened:
                body = smax(body, -self.jet_pipe(), 0.012)
            return (body * self.scale).named('Fuselage' if opened else 'Fuselage, inlet and nozzle closed', S_ASM)
        return self._once(('fus', opened), make)

    def duct_air(self):
        """Inlet duct air from the lip plane to the engine face, real coordinates."""
        return (fmax(self.duct_core(), self.lip_plane()) * self.scale).named('Inlet duct air', S_DUCT)

    def jet_air(self):
        return (fmax(self.jet_pipe(), self.xr - LREF) * self.scale).named('Nozzle air', S_DUCT)

    # ------------------------------------------------------------------ lifting panels
    def _panel(self, name, section, s, n, x0, tan_sweep, length, root_chord, tip_chord, tc_root, tc_tip, root_cut=False):
        """One lifting panel. s runs along the panel from the centreline, n is the distance from its chord plane.
        root_cut ends the panel at s = 0 (the fin, whose root line is inside the body)."""
        te = self.d.m('te_thickness')
        sc = clamp(s, 0.0, length)
        frac = sc / length
        x_le = (sc * tan_sweep + x0).named(name + ' leading-edge station', section)
        chord = ((tip_chord - root_chord) * frac + root_chord).named(name + ' local chord', section)
        thick = (((tc_tip - tc_root) * frac + tc_root) * chord).named(name + ' local thickness', section)
        cps = [(x_le + chord * float(u), thick * float(t) + te * (0.5 * float(u))) for u, t in FOIL_NET]
        sec = spline2d(cps, X, absf(n), label=name + ' section')
        cuts = [sec, X - x_le - chord, s - length] + ([-s] if root_cut else [])
        field = fmax(*cuts).named(name + ' panel', section)
        # kept for the structure: chord fraction and span fraction of any point of the panel
        self.panels[name] = dict(field=field, s=s, n=n, length=length, x_le=x_le, chord=chord, thick=thick)
        return field

    def _pair(self, name, section, prefix, z0_key, cant_key, length, tc_root, tc_tip):
        """Left and right panels (mirrored with |Y|), canted up by an angle from the horizontal."""
        d = self.d
        c, sn = d.cos(cant_key), d.sin(cant_key)
        dz = Z - d.m(z0_key)
        s = (AY * c + dz * sn).named(name + ' span coordinate', section)
        n = (dz * c - AY * sn).named(name + ' normal coordinate', section)
        return self._panel(name, section, s, n, d.station(prefix + '_apex'), d.tan(prefix + '_sweep'), length,
                           d.m(prefix + '_root_chord'), d.m(prefix + '_tip_chord'), tc_root, tc_tip)

    def wing(self):
        def make():
            d = self.d
            length = (d.m('wing_span') * 0.5 / d.cos('wing_dihedral')).named('Wing panel length [m]', S_DIM)
            return self._pair('Wing', S_WING, 'wing', 'wing_height', 'wing_dihedral', length, d.frac('wing_tc_root'), d.frac('wing_tc_tip'))
        return self._once('wing', make)

    def htail(self):
        def make():
            d = self.d
            length = (d.m('htail_span') * 0.5 / d.cos('htail_dihedral')).named('Horizontal tail panel length [m]', S_DIM)
            return self._pair('Horizontal tail', S_TAIL, 'htail', 'htail_height', 'htail_dihedral', length, d.frac('tail_tc'), d.frac('tail_tc'))
        return self._once('htail', make)

    def vtail(self):
        def make():
            d = self.d
            return self._pair('V-tail', S_TAIL, 'vtail', 'vtail_root_height', 'vtail_cant', d.m('vtail_length'), d.frac('tail_tc'), d.frac('tail_tc'))
        return self._once('vtail', make)

    def fin(self):
        def make():
            d = self.d
            s = (Z - d.m('fin_root_height')).named('Fin span coordinate', S_TAIL)
            return self._panel('Fin', S_TAIL, s, AY, d.station('fin_apex'), d.tan('fin_sweep'), d.m('fin_height'),
                               d.m('fin_root_chord'), d.m('fin_tip_chord'), d.frac('tail_tc'), d.frac('tail_tc'), root_cut=True)
        return self._once('fin', make)

    def tail_switch(self):
        """(conventional offset, V-tail offset): the tail set that is not selected is moved out of reach."""
        t = self.d.raw('tail_type')
        return (t * BIG).named('Conventional tail removed when > 0', S_TAIL), ((1.0 - t) * BIG).named('V-tail removed when > 0', S_TAIL)

    def tails(self):
        def make():
            off_c, off_v = self.tail_switch()
            conventional = (fmin(self.fin(), self.htail()) + off_c).named('Conventional tail', S_TAIL)
            vee = (self.vtail() + off_v).named('V-tail', S_TAIL)
            return fmin(conventional, vee).named('Tail surfaces', S_TAIL)
        return self._once('tails', make)

    # ------------------------------------------------------------------ exterior
    def exterior(self, opened=True):
        """The outer mold line. opened=False: inlet and nozzle closed (the flow body for aerodynamics)."""
        def make():
            d = self.d
            wing = self.wing()
            x_le = d.station('wing_apex') + clamp(AY, 0.0, d.m('wing_span') * 0.5) * d.tan('wing_sweep')
            fade = fl.smoothstep(0.05, 0.60, X - x_le)
            fillet = fmax(fade * 0.10, 0.006).named('Wing root fillet size', S_EXT)
            body = sminq(self.fuselage(opened), wing, fillet)
            body = sminq(body, self.tails(), 0.035)
            return body.named('Outer mold line' if opened else 'Flow body (inlet and nozzle closed)', S_EXT)
        return self._once(('ext', opened), make)

    # ------------------------------------------------------------------ sizes for meshing and checks
    def box(self, pad=0.25):
        d = self.d
        L = fl.num(self.L)
        half = 0.5 * max(d.value('wing_span'), d.value('htail_span'), 2 * d.value('vtail_length')) * 0.3048
        top = max(d.value('fin_root_height') * 0.0254 + d.value('fin_height') * 0.3048,
                  d.value('vtail_root_height') * 0.0254 + d.value('vtail_length') * 0.3048, 0.09 * L)
        return [-pad, -half - pad, -0.06 * L * d.value('height_scale') - pad], [1.10 * L + pad, half + pad, top + pad]


def smax_field(a, b, k):
    """Smooth maximum whose blend width k may be a number or a scalar node."""
    a, b = lift(a), lift(b)
    h = fmax(k - absf(a - b), 0.0) / k
    return fmax(a, b) + h * h * (k * 0.25)
