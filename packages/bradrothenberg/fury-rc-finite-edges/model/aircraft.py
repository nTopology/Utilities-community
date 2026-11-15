"""The Fury model: every body of the notebook, built from the outer mold line.

  Skin                     the outer mold line, shelled inward by the skin thickness, with control-surface gaps
  Fuselage frames          ring frames that follow the inner skin (and go round the inlet duct), solid bulkheads at tank ends
  Wing spars, wing ribs    three spars at chord fractions, ribs at span fractions
  Tail structure           spars and ribs of the selected tail set
  Engine, jet pipe         a turbofan envelope of FJ44-4 size on the duct axis, and the pipe to the nozzle
  Fuel                     three fuselage cells between the bulkheads and one cell in each wing box
  Mission systems bay      the usable volume of the forebody
  Air data boom, inlet duct air
  Panel lines, paint, markings, formation lights   model/livery.py

The structure is a representative layout: sensible members in sensible places, sized by the inputs in
"05 Inputs | Structure and fuel". It is not a stressed design.
"""
from __future__ import annotations

import math

import fieldlab as fl
from fieldlab import X, Y, Z, absf, clamp, fmax, fmin
from shapes import G
import oml
from oml import Airframe, AY, LREF, T_FACE, T_ENGINE_REAR, Z_ENGINE
from design import Design, S_DIM
import registry
from livery import Livery

S_STR = '20 Structure'
S_SYS = '30 Engine and systems'
S_FUEL = '31 Fuel'
S_BODY = '40 Bodies'

# stations as fractions of the fuselage length
BULKHEADS = [0.08, 0.345, 0.47, 0.61, T_FACE]            # solid: radome, tank ends, engine firewall
RING_FRAMES = [0.14, 0.20, 0.265, 0.405, 0.54, 0.675, 0.81, 0.87, 0.93]
TANK_CELLS = [('Forward fuselage fuel', 0.345, 0.47), ('Centre fuselage fuel', 0.47, 0.61), ('Aft fuselage fuel', 0.61, T_FACE)]
GEAR_BAY = (0.565, 0.70, 0.004)                           # main gear bay kept free of fuel: from, to, below this height / length
WING_RIBS = [0.28, 0.40, 0.52, 0.64, 0.76, 0.88, 0.975]   # fractions of the wing panel length
WING_TANK_END = 0.64
TAIL_RIBS = [0.45, 0.63, 0.81, 0.97]
FIN_RIBS = [0.22, 0.47, 0.72, 0.96]
ENGINE_LENGTH = 1.742                                     # m (68.6 in), FJ44-4 class
ENGINE_RADIUS = G('Engine envelope radius', [0.0, 0.12, 0.45, 0.62, 0.90, 1.20, 1.46, ENGINE_LENGTH],
                  [0.293, 0.321, 0.321, 0.272, 0.250, 0.240, 0.205, 0.170])
ENGINE_RADIUS.section = S_SYS


class Model:
    def __init__(self, design: Design | None = None):
        self.d = d = design or Design()
        self.af = af = Airframe(d)
        self.L = af.L
        self.skin_t = d.m('skin_thickness')
        self.web = d.m('web_thickness')
        self.clear = d.m('tank_clearance')
        self.exterior = af.exterior(True)
        self.inner = (self.exterior + self.skin_t).named('Inner skin surface', S_STR)
        self.fus_inner = (af.fuselage(True) + self.skin_t).named('Fuselage inner surface', S_STR)
        self.off_conventional, self.off_vee = af.tail_switch()
        af.wing(), af.tails()
        self.livery = Livery(self)

    # ------------------------------------------------------------------ skin
    def gaps(self):
        """Control-surface gaps: narrow grooves along the flaperon and rudder hinge lines."""
        w, depth = 0.006, 0.004
        pw = self.af.panels['Wing']
        hinge = absf(X - pw['x_le'] - pw['chord'] * 0.76) - w / 2
        eta = pw['s'] / pw['length']
        ends = fmin(absf(eta - 0.27), absf(eta - 0.80)) * pw['length'] - w / 2
        flap = fmin(fmax(hinge, 0.27 - eta, eta - 0.80), fmax(ends, pw['x_le'] + pw['chord'] * 0.76 - X))
        pf = self.af.panels['Fin']
        eta_f = pf['s'] / pf['length']
        rudder = fmax(absf(X - pf['x_le'] - pf['chord'] * 0.66) - w / 2, 0.10 - eta_f, eta_f - 0.93) + self.off_conventional
        return fmax(fmin(flap, rudder), -(self.exterior + depth)).named('Control-surface gaps', S_STR)

    def skin(self):
        shell = fmax(self.exterior, -self.inner)
        return fmax(shell, -self.gaps(), -self.livery.grooves()).named('Skin shell', S_STR)

    # ------------------------------------------------------------------ fuselage structure
    def _stations(self, fracs):
        return fmin(*[absf(X - self.L * f) for f in fracs])

    def frames(self):
        ring_depth = (self.L * 0.0075).named('Ring frame depth [m]', S_DIM)
        rings = fmax(self._stations(RING_FRAMES) - self.web * 0.5, -(self.fus_inner + ring_depth)).named('Ring frames (uncut)', S_STR)
        solid = (self._stations(BULKHEADS) - self.web * 0.5).named('Bulkhead planes', S_STR)
        return fmax(fmin(rings, solid), self.fus_inner).named('Fuselage frames and bulkheads', S_STR)

    # ------------------------------------------------------------------ lifting-surface structure
    def _panel_structure(self, name, spar_fracs, rib_fracs, start, section=S_STR):
        """Spars at chord fractions and ribs at span fractions inside one lifting panel.
        start: where the structure begins along the panel (fraction of the panel length)."""
        p = self.af.panels[name]
        inside = p['field'] + self.skin_t
        eta = p['s'] / p['length']
        spars = fmin(*[absf(X - p['x_le'] - p['chord'] * f) for f in spar_fracs]) - self.web * 0.5
        spars = fmax(spars, inside, start - eta, eta - 0.985).named(name + ' spar webs', section)
        front, rear = p['x_le'] + p['chord'] * spar_fracs[0], p['x_le'] + p['chord'] * spar_fracs[-1]
        ribs = fmin(*[absf(eta - f) for f in rib_fracs]) * p['length'] - self.web * 0.5
        ribs = fmax(ribs, inside, front - X, X - rear).named(name + ' rib webs', section)
        return spars, ribs

    def wing_structure(self):
        d = self.d
        fs, rs = d.frac('front_spar'), d.frac('rear_spar')
        return self._panel_structure('Wing', [fs, (fs + rs) * 0.5, rs], WING_RIBS, 0.16)

    def tail_structure(self):
        self.af.tails()
        hs, hr = self._panel_structure('Horizontal tail', [0.25, 0.60], TAIL_RIBS, 0.22)
        fs, fr = self._panel_structure('Fin', [0.25, 0.62], FIN_RIBS, 0.03)
        vs, vr = self._panel_structure('V-tail', [0.25, 0.60], TAIL_RIBS, 0.18)
        conventional = fmin(hs, hr, fs, fr) + self.off_conventional
        vee = fmin(vs, vr) + self.off_vee
        return fmax(fmin(conventional, vee), self.inner).named('Tail spars and ribs', S_STR)

    # ------------------------------------------------------------------ engine
    def engine_axis_height(self):
        return (self.af.scale * self.d.raw('height_scale') * (Z_ENGINE * LREF)).named('Engine axis height [m]', S_DIM)

    def engine(self):
        u = (X - self.L * T_FACE).named('Distance aft of the engine face', S_STR)
        r = fl.length2(Y, Z - self.engine_axis_height())
        return fmax(r - ENGINE_RADIUS(u), -u, u - ENGINE_LENGTH).named('Engine envelope', S_SYS)

    def jet_pipe(self):
        air = self.af.jet_air()
        return fmax(air - 0.004, -air, X - self.L, self.L * T_FACE + ENGINE_LENGTH - 0.02 - X).named('Jet pipe wall', S_SYS)

    # ------------------------------------------------------------------ fuel
    def fuselage_fuel(self):
        """Fuel fills the fuselage between the tank bulkheads, a clearance inside the inner skin and the duct wall,
        outside the frames and the main gear bay."""
        base = self.fus_inner + self.clear
        frames = self.frames() - self.clear * 0.25
        x0, x1, ztop = GEAR_BAY
        gear_bay = fmax(self.L * x0 - X, X - self.L * x1, Z - self.af.scale * self.d.raw('height_scale') * (ztop * LREF)).named('Main gear bay (kept free)', S_FUEL)
        free = fmax(base, -frames, -(gear_bay - self.clear)).named('Fuselage fuel space', S_FUEL)
        cells = []
        for name, a, b in TANK_CELLS:
            cells.append((name, fmax(free, self.L * a + self.clear - X, X - self.L * b + self.clear).named(name + ' cell', S_FUEL)))
        return cells

    def wing_fuel(self):
        d = self.d
        p = self.af.panels['Wing']
        fs, rs = d.frac('front_spar'), d.frac('rear_spar')
        eta = p['s'] / p['length']
        spars, ribs = self.wing_structure()
        box = fmax(p['field'] + self.skin_t + self.clear * 0.5, p['x_le'] + p['chord'] * fs + self.clear * 0.5 - X,
                   X - p['x_le'] - p['chord'] * rs + self.clear * 0.5, eta - WING_TANK_END)
        side = (self.fus_inner + self.clear)                    # the wing cell starts where the fuselage cells end
        return fmax(box, -side, -(fmin(spars, ribs) - self.clear * 0.25)).named('Wing fuel cell', S_FUEL)

    # ------------------------------------------------------------------ systems
    def mission_bay(self):
        return fmax(self.fus_inner + 0.04, self.L * 0.095 - X, X - self.L * 0.255).named('Mission systems bay volume', S_SYS)

    def boom(self):
        z = self.af.scale * (0.0045 * LREF)
        r = fl.length2(Y, Z - z)
        tip = self.L * -0.118
        radius = clamp((X - tip) * 0.25 + 0.004, 0.004, 0.017)
        return fmax(r - radius, tip - X, X - self.L * 0.03).named('Air data boom', S_SYS)

    # ------------------------------------------------------------------ registry
    def boxes(self):
        """Bounding boxes of the bodies (metres), from the current inputs."""
        d, L = self.d, fl.num(self.L)
        lo, hi = self.af.box()
        ws, hs = d.value('width_scale'), d.value('height_scale')
        half_w, top, bottom = 0.085 * L * ws, 0.085 * L * hs, -0.055 * L * hs
        wing_x0 = d.value('wing_apex') * 0.01 * L
        wing_half = d.value('wing_span') * 0.5 * 0.3048
        wing_x1 = wing_x0 + max(d.value('wing_root_chord') * 0.3048, wing_half * abs(math.tan(math.radians(d.value('wing_sweep')))) + d.value('wing_tip_chord') * 0.3048)
        droop = wing_half * 0.12 + 0.12
        return dict(
            all=(lo, hi),
            skin=([-0.13 * L - 0.05, lo[1], lo[2]], hi),
            fuselage=([-0.02, -half_w, bottom], [L + 0.02, half_w, top]),
            wing=([wing_x0 - 0.05, -wing_half - 0.03, d.value('wing_height') * 0.0254 - droop], [wing_x1 + 0.05, wing_half + 0.03, d.value('wing_height') * 0.0254 + droop]),
            tail=([0.76 * L, lo[1], -0.02 * L], [hi[0], hi[1], hi[2]]),
            engine=([T_FACE * L - 0.02, -0.36, Z_ENGINE * L * hs - 0.36], [L + 0.02, 0.36, Z_ENGINE * L * hs + 0.36]),
            boom=([-0.13 * L, -0.05, -0.05], [0.04 * L, 0.05, 0.10]),
        )

    def build(self):
        ac = registry.Aircraft()
        B = self.boxes()

        def add(name, field, mat, box, h, group):
            ac.add(name, field, mat, S_BODY, B[box][0], B[box][1], h, group)

        add('Skin', self.skin(), 'skin', 'skin', 0.006, 'skin')
        add('Fuselage frames', self.frames(), 'primer', 'fuselage', 0.003, 'structure')
        spars, ribs = self.wing_structure()
        add('Wing spars', fmax(spars, self.inner), 'primer', 'wing', 0.0025, 'structure')
        add('Wing ribs', fmax(ribs, self.inner), 'primer', 'wing', 0.0025, 'structure')
        add('Tail structure', self.tail_structure(), 'primer', 'tail', 0.0025, 'structure')
        add('Engine', self.engine(), 'engine', 'engine', 0.005, 'systems')
        add('Jet pipe', self.jet_pipe(), 'engine_hot', 'engine', 0.002, 'systems')
        for name, cell in self.fuselage_fuel():
            add(name, cell, 'fuel', 'fuselage', 0.007, 'fuel')
        add('Wing fuel', self.wing_fuel(), 'fuel', 'wing', 0.005, 'fuel')
        add('Mission systems bay', self.mission_bay(), 'avionics', 'fuselage', 0.007, 'systems')
        add('Air data boom', self.boom(), 'skin_dark', 'boom', 0.002, 'skin')
        add('Inlet duct air', self.af.duct_air(), 'duct', 'fuselage', 0.006, 'air')
        for name, field, mat in self.livery.bodies():
            add(name, field, mat, 'skin', 0.002, 'paint')
        return ac


registry.MAT['fuel'] = ((0.85, 0.55, 0.12), 0.45, 0.0)
registry.MAT['skin'] = (Livery.BASE, 0.55, 0.0)
registry.MAT['panel_line'] = ((0.16, 0.17, 0.18), 0.7, 0.0)
registry.MAT['paint_dark'] = (Livery.COLORS['dark'], 0.55, 0.0)
registry.MAT['mark_light'] = (Livery.COLORS['light'], 0.5, 0.0)
registry.MAT['mark_dark'] = (Livery.COLORS['darkmark'], 0.55, 0.0)
registry.MAT['formation'] = (Livery.COLORS['lights'], 0.4, 0.0)


def build(design: Design | None = None):
    m = Model(design)
    ac = m.build()
    ac.model = m
    return ac
