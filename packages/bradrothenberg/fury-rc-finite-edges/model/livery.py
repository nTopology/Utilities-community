"""Panel lines, paint and markings of the Fury model.

Everything here is a pattern: a field that is negative where the pattern is, drawn in a flat view (side, plan or
the plane of a lifting panel) and pushed straight through the aircraft. A pattern becomes a body where it meets
a thin layer on the outer mold line:

  Panel lines                 grooves cut into the skin, and a dark body that fills them so they show
  Paint, dark grey            the stepped dark band on the upper fuselage and the dark tail panels
  Markings, light / dark      designation, tail code, serial, service lettering, national insignia
  Formation lights            the yellow-green strips, and the jet inlet warning triangles in the same colour

The scheme follows US Air Force photographs 04, 05, 06, 07 and 17 (reference/SOURCES.md): two greys, "YFQ-44A" on
the dark band, tail code AI and a serial on the fin, the national insignia on the wings. Positions and sizes are
read from the photographs as fractions of the length; lettering is a plain stroke font, not the real typeface.
The manufacturer's logo and the Air Force wings symbol are not reproduced (a plain star with wing bars stands
where the symbol is).
"""
from __future__ import annotations

import math

import fieldlab as fl
from fieldlab import X, Y, Z, absf, clamp, fmax, fmin
from oml import AY, LREF, T_FACE, HALF_WIDTH
from design import S_DIM

S_PANEL = '21 Panel lines'
S_PAINT = '22 Paint and markings'

# panel breaks of the fuselage, fractions of the length (at frames and bulkheads)
FUSELAGE_BREAKS = [0.08, 0.14, 0.20, 0.345, 0.47, 0.61, T_FACE, 0.87]
# doors and hatches: name, from station, to station, inner and outer half breadth (fractions of the length), +1 top / -1 underside
DOORS = [('Avionics hatch', 0.105, 0.185, 0.0, 0.011, 1),
         ('Engine bay door', 0.765, 0.905, 0.0, 0.020, -1)]
WING_RIB_LINES = [0.40, 0.64, 0.88]
FILM = 0.0005                # paint and markings are drawn as a layer this far above the outer mold line [m]

# stroke font: glyph width and strokes (polylines) in units of the letter height
GLYPHS = {
    'A': (0.6, [[(0, 0), (0, 0.7), (0.3, 1), (0.6, 0.7), (0.6, 0)], [(0, 0.38), (0.6, 0.38)]]),
    'C': (0.6, [[(0.6, 1), (0, 1), (0, 0), (0.6, 0)]]),
    'E': (0.6, [[(0.6, 1), (0, 1), (0, 0), (0.6, 0)], [(0, 0.5), (0.45, 0.5)]]),
    'F': (0.6, [[(0.6, 1), (0, 1), (0, 0)], [(0, 0.5), (0.45, 0.5)]]),
    'I': (0.0, [[(0, 0), (0, 1)]]),
    'O': (0.6, [[(0, 0), (0.6, 0), (0.6, 1), (0, 1), (0, 0)]]),
    'Q': (0.6, [[(0, 0), (0.6, 0), (0.6, 1), (0, 1), (0, 0)], [(0.36, 0.30), (0.68, -0.08)]]),
    'R': (0.6, [[(0, 0), (0, 1), (0.6, 1), (0.6, 0.5), (0, 0.5)], [(0.25, 0.5), (0.6, 0)]]),
    'S': (0.6, [[(0.6, 1), (0, 1), (0, 0.5), (0.6, 0.5), (0.6, 0), (0, 0)]]),
    'U': (0.6, [[(0, 1), (0, 0), (0.6, 0), (0.6, 1)]]),
    'Y': (0.6, [[(0, 1), (0.3, 0.5), (0.6, 1)], [(0.3, 0.5), (0.3, 0)]]),
    '0': (0.6, [[(0, 0), (0.6, 0), (0.6, 1), (0, 1), (0, 0)]]),
    '1': (0.3, [[(0.0, 0.75), (0.3, 1), (0.3, 0)]]),
    '4': (0.6, [[(0.45, 0), (0.45, 1), (0, 0.33), (0.6, 0.33)]]),
    '-': (0.5, [[(0.05, 0.5), (0.45, 0.5)]]),
    '.': (0.0, [[(0, 0), (0, 0.02)]]),
}


def lettering(string, u, v, height, stroke=0.15, gap=0.30):
    """Distance field of a line of text, centred on (u, v) = (0, 0), reading along +u, letters `height` tall.
    Every stroke is a straight segment; the text is the nearest segment distance minus half the stroke width."""
    segs, pen = [], 0.0
    for ch in string:
        if ch == ' ':
            pen += 0.5
            continue
        width, strokes = GLYPHS[ch]
        for poly in strokes:
            segs += [((pen + a[0], a[1]), (pen + b[0], b[1])) for a, b in zip(poly, poly[1:])]
        pen += width + gap
    total = pen - gap
    d2 = []
    for (ax, ay), (bx, by) in segs:
        ax, bx = (ax - total / 2) * height, (bx - total / 2) * height
        ay, by = (ay - 0.5) * height, (by - 0.5) * height
        if abs(ay - by) < 1e-12:
            du, dv = u - clamp(u, min(ax, bx), max(ax, bx)), v - ay
        elif abs(ax - bx) < 1e-12:
            du, dv = u - ax, v - clamp(v, min(ay, by), max(ay, by))
        else:
            ex, ey = bx - ax, by - ay
            k = 1.0 / (ex * ex + ey * ey)
            t = clamp((u - ax) * (ex * k) + (v - ay) * (ey * k), 0.0, 1.0)
            du, dv = u - ax - t * ex, v - ay - t * ey
        d2.append(du * du + dv * dv)
    return fl.sqrt(fmin(*d2)) - 0.5 * stroke * height


def star(u, v, radius):
    """Five-pointed star, one point along +v. A point is in the star when it is inside at least four of the five
    edge lines of the pentagram."""
    d = radius * math.cos(math.radians(72))
    h = [u * math.cos(math.radians(90 + 72 * k)) + v * math.sin(math.radians(90 + 72 * k)) - d for k in range(5)]
    return fmax(*[fmin(h[i], h[j]) for i in range(5) for j in range(i + 1, 5)])


class Livery:
    BASE = (0.63, 0.65, 0.67)
    COLORS = dict(dark=(0.37, 0.39, 0.41), light=(0.84, 0.85, 0.86), darkmark=(0.30, 0.31, 0.33), lights=(0.80, 0.83, 0.42), line=0.50)

    def __init__(self, model):
        self.m, self.af, self.d = model, model.af, model.d
        af = self.af
        self.E = model.oml                  # the outer mold line before the landing gear bays are cut
        self.w = self.d.m('panel_line_width')
        self.depth = self.d.m('panel_line_depth')
        # fuselage patterns are drawn on the reference aircraft, so they scale with the fuselage inputs
        self.x, self.y, self.z = af.xr, af.yr, af.zr
        self.side = clamp(Y * 1.0e4, -1.0, 1.0).named('Side of the aircraft (+1 right, -1 left)', S_PAINT)
        self.near_fuselage = (af.fuselage(True) - 0.03).named('Near the fuselage', S_PANEL)
        self._memo = {}

    def _once(self, key, make):
        if key not in self._memo:
            self._memo[key] = make()
        return self._memo[key]

    # ------------------------------------------------------------------ panel lines
    def _line(self, f):
        return absf(f) - self.w * 0.5

    def fuselage_lines(self):
        x, y, z, K = self.x, self.y, self.z, LREF
        rings = self._line(fmin(*[absf(x - t * K) for t in FUSELAGE_BREAKS])).named('Fuselage panel breaks at the frames', S_PANEL)
        half = HALF_WIDTH(x)
        dorsal = fmax(self._line(y - half * 0.42), 0.14 * K - x, x - 0.80 * K, 0.02 * K - z).named('Dorsal panel edge', S_PANEL)
        ventral = fmax(self._line(y - half * 0.30), 0.30 * K - x, x - 0.93 * K, z + 0.01 * K).named('Ventral panel edge', S_PANEL)
        doors = []
        for name, x0, x1, y0, y1, top in DOORS:
            box = fmax(absf(x - 0.5 * (x0 + x1) * K) - 0.5 * (x1 - x0) * K, absf(y - 0.5 * (y0 + y1) * K) - 0.5 * (y1 - y0) * K)
            doors.append(fmax(self._line(box), (0.02 * K - z) if top > 0 else (z + 0.005 * K)).named(name + ' outline', S_PANEL))
        # landing gear doors: the outlines of the bays (model/gear.py), on the underside
        doors.append(fmax(self._line(self.m.gear.outlines()), z + 0.005 * K).named('Landing gear door outlines', S_PANEL))
        # panel lines belong on the outside: none on the walls of the inlet duct, which the flat patterns also pass through
        outside_duct = (0.012 - self.af.duct_air()).named('Outside the inlet duct when < 0', S_PANEL)
        return fmax(fmin(rings, dorsal, ventral, *doors), self.near_fuselage, outside_duct).named('Fuselage panel lines', S_PANEL)

    def _panel_lines(self, name, chord_fracs, span_fracs, start, tip_cap):
        """Lines along the spars (chord fractions) and along ribs (span fractions) of one lifting panel."""
        p = self.af.panels[name]
        eta = p['s'] / p['length']
        chordwise = fmin(*[absf(X - p['x_le'] - p['chord'] * f) for f in chord_fracs])
        lines = fmax(self._line(chordwise), start - eta)
        if span_fracs:
            front, rear = p['x_le'] + p['chord'] * chord_fracs[0], p['x_le'] + p['chord'] * chord_fracs[-1]
            ribs = fmax(self._line(fmin(*[absf(eta - f) for f in span_fracs]) * p['length']), front - X, X - rear)
            lines = fmin(lines, ribs)
        cap = self._line((eta - tip_cap) * p['length'])
        return fmax(fmin(lines, cap), p['field'] - 0.01).named(name + ' panel lines', S_PANEL)

    def lines(self):
        def make():
            d, m = self.d, self.m
            fs, rs = d.frac('front_spar'), d.frac('rear_spar')
            wing = self._panel_lines('Wing', [0.08, fs, rs], WING_RIB_LINES, 0.26, 0.975)
            htail = self._panel_lines('Horizontal tail', [0.25, 0.60], [0.63], 0.30, 0.97)
            fin = self._panel_lines('Fin', [0.25], [], 0.10, 0.93)
            vee = self._panel_lines('V-tail', [0.25, 0.60], [0.63], 0.22, 0.97)
            tails = fmin(fmin(htail, fin) + m.off_conventional, vee + m.off_vee)
            return fmin(self.fuselage_lines(), wing, tails).named('Panel line pattern', S_PANEL)
        return self._once('lines', make)

    def grooves(self):
        """The panel line pattern from the outer surface down to the groove depth (open to the outside)."""
        return fmax(self.lines(), -(self.E + self.depth)).named('Panel grooves', S_PANEL)

    def line_body(self):
        return fmax(self.lines(), -(self.E + self.depth), self.E).named('Panel line fill', S_PANEL)

    # ------------------------------------------------------------------ paint
    def _layer(self, pattern, k):
        """A pattern as a thin body on the outer mold line, k paint films thick, with the panel lines left open."""
        return fmax(pattern, self.E - FILM * k, -(self.E + FILM), -self.lines())

    def dark_pattern(self):
        def make():
            x, z, K = self.x, self.z, LREF

            def ramp(a, b):
                return clamp((x - a * K) * (1.0 / ((b - a) * K)), 0.0, 1.0)
            low = (0.050 * K - 0.010 * K * ramp(0.40, 0.41) - 0.014 * K * ramp(0.52, 0.534) + 0.019 * K * ramp(0.74, 0.759)).named('Dark band lower edge height', S_PAINT)
            band = fmax(low - z, 0.22 * K + (0.070 * K - z) - x, x - 0.86 * K, self.near_fuselage).named('Dark band on the upper fuselage', S_PAINT)
            p = self.af.panels['Horizontal tail']
            eta = p['s'] / p['length']
            u = (X - p['x_le']) / p['chord']
            tail = fmax(absf(u - 0.40) - 0.22, absf(eta - 0.60) - 0.20, -p['n'], p['field'] - 0.01) + self.m.off_conventional
            return fmin(band, tail.named('Dark panel on the horizontal tail', S_PAINT)).named('Dark grey pattern', S_PAINT)
        return self._once('dark', make)

    def _side_text(self, string, station, height_at, letter, label):
        """Text on the side of the aircraft, read from outside on both sides. station, height_at, letter: fractions of the length."""
        u = (self.side * (station * LREF - self.x)).named(label + ' | along the text', S_PAINT)
        v = (self.z - height_at * LREF).named(label + ' | up the text', S_PAINT)
        # the window keeps the text at its own station (on the centreline the two sides meet and `side` passes through zero)
        window = absf(self.x - station * LREF) - 0.5 * letter * LREF * (0.9 * len(string) + 1.0)
        return fmax(lettering(string, u, v, letter * LREF), window).named(label, S_PAINT)

    def light_markings(self):
        def make():
            K = LREF
            designation = fmax(self._side_text('YFQ-44A', 0.600, 0.0385, 0.0125, 'Lettering YFQ-44A'), self.near_fuselage)
            code = self._side_text('AI', 0.915, 0.115, 0.020, 'Tail code AI')
            serial = self._side_text('1001', 0.897, 0.083, 0.011, 'Serial 1001')
            # conventional tail: only on the fin. V-tail: the letters fall on the two canted panels
            on_fin = fmin((self.y - 0.012 * K) + self.m.off_conventional, self.m.off_vee - 1.0)
            tail = fmax(fmin(code, serial), on_fin).named('Tail markings', S_PAINT)
            # winged star on the aft fuselage side (stands in for the Air Force symbol)
            u = (self.x - 0.795 * K).named('Winged star | along', S_PAINT)
            v = (self.z - 0.004 * K).named('Winged star | up', S_PAINT)
            r = 0.0085 * K
            wings = fmin(*[fmax(absf(v - (0.9 + 0.75 * i) * r - absf(u) * 0.55) - 0.24 * r, absf(u) - (1.5 + 0.55 * i) * r, (0.25 * r) - absf(u)) for i in range(3)])
            symbol = fmax(fmin(star(u, v + 0.35 * r, r), wings), self.near_fuselage).named('Winged star', S_PAINT)
            return fmin(designation, tail, symbol).named('Light markings pattern', S_PAINT)
        return self._once('light', make)

    def insignia(self):
        """National insignia (star in a disc with two bars) on the upper left and lower right wing."""
        d = self.d
        p = self.af.panels['Wing']
        s_c = p['length'] * 0.60
        chord_c = d.m('wing_root_chord') + (d.m('wing_tip_chord') - d.m('wing_root_chord')) * 0.60
        u = (AY - s_c * d.cos('wing_dihedral')).named('Insignia | along the span', S_PAINT)
        v = (d.station('wing_apex') + s_c * d.tan('wing_sweep') + chord_c * 0.45 - X).named('Insignia | forward', S_PAINT)
        r = (chord_c * 0.14).named('Insignia radius [m]', S_DIM)
        disc = fl.length2(u, v) - r
        bars = fmax(absf(absf(u) - r * 1.5) - r * 0.5, absf(v + r * 0.05) - r * 0.25)
        mark = fmin(fmax(disc, -star(u, v, r)), bars)
        return fmax(mark, self.side * p['n'] * 50.0, p['field'] - 0.01).named('National insignia', S_PAINT)

    def dark_markings(self):
        def make():
            K = LREF
            # service lettering on the slanted lower side of the fuselage behind the main gear bay, drawn in the plan view:
            # it shows from the side and from below [photographs 01 and 16]
            u = (self.side * (0.670 * K - self.x)).named('Lettering U.S. AIR FORCE | along the text', S_PAINT)
            v = (self.y - 0.047 * K).named('Lettering U.S. AIR FORCE | up the text', S_PAINT)
            window = absf(self.x - 0.670 * K) - 0.055 * K
            service = fmax(lettering('U.S. AIR FORCE', u, v, 0.0080 * K), window, self.z + 0.012 * K, self.near_fuselage).named('Lettering U.S. AIR FORCE', S_PAINT)
            return fmin(service, self.insignia(), self.side_details()).named('Dark markings pattern', S_PAINT)
        return self._once('darkmarks', make)

    def side_details(self):
        """Small dark details on the fuselage sides, drawn in the side view [photographs 13, 19, 23, 25]: a cooling air
        grille and a flush scoop on the forebody, and a row of louvres above the wing root."""
        x, z, K = self.x, self.z, LREF
        lean = (z - 0.020 * K) * 0.55                               # the details lean back like the paint band edges
        grille = fmax(absf(x - lean - 0.300 * K) - 0.012 * K, absf(z - 0.021 * K) - 0.0065 * K)
        slats = absf(absf(z - 0.021 * K) - 0.0033 * K) - 0.0006 * K  # two light slats left across the grille
        grille = fmax(grille, -slats)
        # flush scoop: a triangle with its point forward
        u = x - 0.222 * K
        scoop = fmax(-u, u - 0.030 * K, absf(z - 0.0165 * K) - u * 0.16)
        # louvres: four short slanted slots
        louvres = fmin(*[fmax(absf(x - lean - (0.452 + 0.007 * i) * K) - 0.0011 * K, absf(z - 0.0335 * K) - 0.0035 * K) for i in range(4)])
        return fmax(fmin(grille, scoop, louvres), self.near_fuselage).named('Grille, flush scoop and louvres', S_PAINT)

    def inlet_warning(self):
        """The jet inlet warning triangle on each side of the cowl, just behind the inlet lip [photograph 36]: an outline
        triangle with its point down and a small solid triangle inside. Drawn in the side view. The cowl wall leans about
        45 deg, so heights are stretched by 1.41 to give a triangle of equal sides on the wall. The wording is left out."""
        K = LREF
        u = (self.x - 0.337 * K).named('Inlet warning | along', S_PAINT)
        w = ((self.z + 0.0150 * K) * 1.41).named('Inlet warning | up the cowl wall', S_PAINT)

        def triangle(w, r):                                          # point down, r = radius of the inscribed circle
            return fmax(w, 0.866 * absf(u) - 0.5 * w) - r
        outline = absf(triangle(w, 0.0065 * K) + 0.0011 * K) - 0.00055 * K
        mark = fmin(outline, triangle(w + 0.0030 * K, 0.0011 * K))
        on_cowl = absf(self.af.fuselage(False)) - 0.004               # the outside of the cowl, not the duct wall behind it
        return fmax(mark, on_cowl).named('Inlet warning triangle', S_PAINT)

    def lights_pattern(self):
        def make():
            x, z, K = self.x, self.z, LREF

            def strip(x0, x1, z0, z1):
                return fmax(absf(x - 0.5 * (x0 + x1) * K) - 0.5 * (x1 - x0) * K, absf(z - 0.5 * (z0 + z1) * K) - 0.5 * (z1 - z0) * K)
            fwd = fmax(strip(0.170, 0.212, 0.0195, 0.0225), self.near_fuselage)
            aft = fmax(strip(0.765, 0.805, 0.0530, 0.0560), self.near_fuselage)
            fin = strip(0.955, 0.988, 0.1850, 0.1880) + self.m.off_conventional
            return fmin(fwd, aft, fin, self.inlet_warning()).named('Formation light pattern', S_PAINT)
        return self._once('lights', make)

    def bodies(self):
        """(name, field, material) of the bodies added to the notebook."""
        return [('Panel lines', self.line_body(), 'panel_line'),
                ('Paint, dark grey', self._layer(self.dark_pattern(), 1.0).named('Dark grey paint layer', S_PAINT), 'paint_dark'),
                ('Markings, light', self._layer(self.light_markings(), 2.0).named('Light markings layer', S_PAINT), 'mark_light'),
                ('Markings, dark', self._layer(self.dark_markings(), 2.0).named('Dark markings layer', S_PAINT), 'mark_dark'),
                ('Formation lights', self._layer(self.lights_pattern(), 2.0).named('Formation light layer', S_PAINT), 'formation')]

    # ------------------------------------------------------------------ host colouring (previews)
    def colour(self, pts, registry):
        """RGB of the paint at surface points (N x 3, metres): base grey, dark pattern, markings, lights, panel lines."""
        import numpy as np
        rgb = np.tile(np.array(self.BASE, np.float32), (len(pts), 1))
        on_oml = np.abs(registry.values_at(self.E, pts)) < 0.004          # not the walls of the landing gear bays
        for field, key in ((self.dark_pattern(), 'dark'), (self.light_markings(), 'light'), (self.dark_markings(), 'darkmark'), (self.lights_pattern(), 'lights')):
            rgb[on_oml & (registry.values_at(field, pts) < 0)] = self.COLORS[key]
        rgb[on_oml & (registry.values_at(self.lines(), pts) < 0)] *= self.COLORS['line']
        return rgb
