"""Design inputs of the Fury model.

One table. Every row becomes a named number in the notebook (sections 01 to 05) and a constant
on the host. The geometry never uses a bare number for anything a designer would want to change:
it asks this module.

Units: inputs are in the units an aircraft designer reads (ft, in, deg, percent). The model works
in metres and radians, so every input is converted once, in the notebook section
"07 Derived dimensions", and the geometry uses the converted values.

Where the numbers come from: reference/DATA.md and reference/PROPORTIONS.md (public photographs,
measured as fractions of the fuselage length), and docs/MATCH.md for the comparison.
"""
from __future__ import annotations

import math

import fieldlab as fl

FT, IN, DEG = 0.3048, 0.0254, math.pi / 180.0

S_FUS = '01 Inputs | Fuselage'
S_WING = '02 Inputs | Wing'
S_TAIL = '03 Inputs | Tail'
S_PROP = '04 Inputs | Inlet, duct and engine'
S_STR = '05 Inputs | Structure and fuel'
S_GEAR = '06 Inputs | Landing gear and stores'
S_DIM = '07 Derived dimensions'

# key: (notebook name, value, section, what it does)
INPUTS = {
    # ---------------------------------------------------------------- fuselage
    'length': ('Fuselage length [ft]', 33.5, S_FUS, 'Nose tip to nozzle exit. Every fuselage station scales with it.'),
    'width_scale': ('Fuselage width scale [-]', 1.0, S_FUS, 'Multiplies every fuselage half width. 1 = as the reference aircraft.'),
    'height_scale': ('Fuselage height scale [-]', 1.0, S_FUS, 'Multiplies every fuselage height and depth. 1 = as the reference aircraft.'),
    # ---------------------------------------------------------------- wing
    'wing_span': ('Wing span [ft]', 24.85, S_WING, 'Tip to tip.'),
    'wing_root_chord': ('Wing root chord [ft]', 9.94, S_WING, 'Chord on the aircraft centreline (the wing is continued to the centreline inside the body).'),
    'wing_tip_chord': ('Wing tip chord [ft]', 1.64, S_WING, 'Chord at the tip.'),
    'wing_sweep': ('Wing leading-edge sweep [deg]', 31.0, S_WING, 'Sweep of the leading edge, positive aft.'),
    'wing_apex': ('Wing apex station [% length]', 38.8, S_WING, 'Where the leading edge would meet the centreline, as a percentage of the fuselage length.'),
    'wing_height': ('Wing height [in]', 5.5, S_WING, 'Height of the wing chord plane above the fuselage reference line. The chine is 4 in above that line, so the chine runs into the wing leading edge.'),
    'wing_dihedral': ('Wing dihedral [deg]', -1.5, S_WING, 'Positive tips up.'),
    'wing_tc_root': ('Wing thickness at root [% chord]', 8.0, S_WING, 'Maximum thickness of the section on the centreline.'),
    'wing_tc_tip': ('Wing thickness at tip [% chord]', 5.0, S_WING, 'Maximum thickness of the section at the tip.'),
    # ---------------------------------------------------------------- tail
    'tail_type': ('Tail type (0 = conventional, 1 = V-tail)', 0.0, S_TAIL, '0 builds a fin and two horizontal tails. 1 builds two canted V-tail panels instead.'),
    'htail_span': ('Horizontal tail span [ft]', 12.73, S_TAIL, 'Tip to tip (conventional tail).'),
    'htail_root_chord': ('Horizontal tail root chord [ft]', 6.2, S_TAIL, 'Chord on the centreline.'),
    'htail_tip_chord': ('Horizontal tail tip chord [ft]', 1.47, S_TAIL, 'Chord at the tip.'),
    'htail_sweep': ('Horizontal tail leading-edge sweep [deg]', 34.0, S_TAIL, 'Positive aft.'),
    'htail_apex': ('Horizontal tail apex station [% length]', 80.7, S_TAIL, 'Leading edge on the centreline, percentage of the fuselage length.'),
    'htail_height': ('Horizontal tail height [in]', 8.9, S_TAIL, 'Height of the tail plane above the fuselage reference line.'),
    'htail_dihedral': ('Horizontal tail dihedral [deg]', 0.0, S_TAIL, 'Positive tips up, negative for anhedral.'),
    'fin_height': ('Fin height [ft]', 4.87, S_TAIL, 'From the fin root line to the fin tip (conventional tail).'),
    'fin_root_chord': ('Fin root chord [ft]', 4.97, S_TAIL, 'Chord on the fin root line.'),
    'fin_tip_chord': ('Fin tip chord [ft]', 2.12, S_TAIL, 'Chord at the fin tip.'),
    'fin_sweep': ('Fin leading-edge sweep [deg]', 45.0, S_TAIL, 'Positive aft.'),
    'fin_apex': ('Fin apex station [% length]', 80.5, S_TAIL, 'Leading edge at the fin root line, percentage of the fuselage length.'),
    'fin_root_height': ('Fin root height [in]', 21.2, S_TAIL, 'Height of the fin root line above the reference line. Keep it inside the body.'),
    'vtail_cant': ('V-tail cant angle [deg]', 47.0, S_TAIL, 'Angle of each V-tail panel above the horizontal.'),
    'vtail_length': ('V-tail panel length [ft]', 6.59, S_TAIL, 'Root to tip along the panel (V-tail).'),
    'vtail_root_chord': ('V-tail root chord [ft]', 5.81, S_TAIL, 'Chord on the centreline.'),
    'vtail_tip_chord': ('V-tail tip chord [ft]', 1.62, S_TAIL, 'Chord at the tip.'),
    'vtail_sweep': ('V-tail leading-edge sweep [deg]', 38.0, S_TAIL, 'Positive aft, measured in the plane of the panel.'),
    'vtail_apex': ('V-tail apex station [% length]', 80.5, S_TAIL, 'Leading edge on the centreline, percentage of the fuselage length.'),
    'vtail_root_height': ('V-tail root height [in]', 10.1, S_TAIL, 'Height of the V vertex above the reference line. Keep it inside the body.'),
    'tail_tc': ('Tail thickness [% chord]', 5.0, S_TAIL, 'Maximum thickness of every tail section.'),
    'te_thickness': ('Trailing-edge thickness [in]', 0.25, S_TAIL, 'Finite thickness of every wing and tail trailing edge.'),
    # ---------------------------------------------------------------- inlet, duct, engine
    'inlet_station': ('Inlet lip station [% length]', 29.5, S_PROP, 'Station of the lower inlet lip on the centreline, percentage of the fuselage length.'),
    'inlet_rake': ('Inlet face lean [deg]', 48.0, S_PROP, 'The inlet face leans forward from the lower lip up to the splitter plate by this angle from vertical.'),
    'inlet_lip_sweep': ('Inlet lip sweep [deg]', 7.0, S_PROP, 'Turns each half of the inlet face back from the centreline, so the face is two facets with a crease on the centreline. With the leaning face and the V-shaped upper lip, about 7 deg makes the upper lip straight across in plan (estimated from photograph 37).'),
    'lip_dihedral': ('Upper lip V angle [deg]', 6.0, S_PROP, 'The upper lip (the splitter plate) is a shallow V, lowest on the centreline. This is the rise of each half from level (estimated from photograph 37).'),
    'diverter_height': ('Diverter height [in]', 1.5, S_PROP, 'Gap between the forebody underside and the splitter plate: the slot that carries the forebody boundary layer past the inlet.'),
    'splitter_thickness': ('Splitter plate thickness [in]', 1.0, S_PROP, 'Thickness of the splitter plate: the top wall of the cowl and the upper lip of the inlet.'),
    'splitter_overhang': ('Splitter plate overhang [in]', 0.0, S_PROP, 'How far the splitter plate (the upper lip) stands ahead of the inlet face. 0 on the aircraft: all the lips lie in the face.'),
    'diverter_sweep': ('Diverter wedge sweep [deg]', 50.0, S_PROP, 'Sweep of the wedge that closes the diverter slot behind the inlet lip and turns the boundary layer out to the sides.'),
    'lip_thickness': ('Inlet lip thickness [in]', 1.0, S_PROP, 'Wall between the outer cowl and the duct at the lip.'),
    'nozzle_diameter': ('Nozzle exit diameter [in]', 16.8, S_PROP, 'Inner diameter of the exhaust nozzle at the exit.'),
    # ---------------------------------------------------------------- structure and fuel
    'skin_thickness': ('Skin thickness [in]', 0.12, S_STR, 'Thickness of the outer skin. Representative, not stressed.'),
    'web_thickness': ('Frame and spar web thickness [in]', 0.20, S_STR, 'Thickness of frames, ribs and spar webs. Representative, not stressed.'),
    'front_spar': ('Wing front spar [% chord]', 18.0, S_STR, 'Front spar position along the local chord.'),
    'rear_spar': ('Wing rear spar [% chord]', 68.0, S_STR, 'Rear spar position along the local chord.'),
    'tank_clearance': ('Fuel tank wall clearance [in]', 1.0, S_STR, 'Gap between a fuel tank and the structure or skin around it.'),
    'panel_line_width': ('Panel line width [in]', 0.25, S_STR, 'Width of the grooves that divide the skin into panels. Drawn wider than a real gap so it shows.'),
    'panel_line_depth': ('Panel line depth [in]', 0.05, S_STR, 'Depth of the panel grooves below the outer surface. Keep it below the skin thickness.'),
    # ---------------------------------------------------------------- landing gear
    'gear_down': ('Landing gear (1 = down, 0 = retracted)', 1.0, S_GEAR, '1 builds the gear, opens the bays and hangs the doors. 0 removes the gear and closes the bays.'),
    'nose_gear_station': ('Nose gear station [% length]', 35.2, S_GEAR, 'Station of the nose wheel axle.'),
    'main_gear_station': ('Main gear station [% length]', 59.2, S_GEAR, 'Station of the main wheel axles.'),
    'gear_track': ('Main gear track [in]', 67.5, S_GEAR, 'Distance between the centres of the two main wheels.'),
    'ground_line': ('Ground line below the reference line [in]', 47.0, S_GEAR, 'How far the ground is below the fuselage reference line with the aircraft standing on its wheels. Sets the leg lengths.'),
    'main_tyre_diameter': ('Main tyre diameter [in]', 19.0, S_GEAR, 'Outer diameter of a main tyre. The width follows.'),
    'wing_stores': ('Wing stores (1 = pylons, rails and missiles, 0 = clean wing)', 1.0, S_GEAR, '1 hangs a pylon with a launch rail and a missile-sized dummy under each wing, as in most photographs. 0 leaves the wing clean.'),
    'nose_tyre_diameter': ('Nose tyre diameter [in]', 14.5, S_GEAR, 'Outer diameter of the nose tyre. The width follows.'),
}


class Design:
    """The inputs at their current values, as field-graph nodes.

    d.raw('wing_span')      the input as entered (ft, in, deg, percent)
    d.m('wing_span')        the same length in metres
    d.rad('wing_sweep'), d.tan('wing_sweep'), d.sin(...), d.cos(...)
    d.station('wing_apex')  a '% length' input as a station in metres
    d.frac('front_spar')    a percentage as a fraction
    d.value('wing_span')    plain float, as entered
    """

    def __init__(self, **overrides):
        unknown = set(overrides) - set(INPUTS)
        assert not unknown, unknown
        self.values = {k: float(overrides.get(k, v[1])) for k, v in INPUTS.items()}

    def value(self, key):
        return self.values[key]

    def raw(self, key):
        name, _, section, _ = INPUTS[key]
        return fl.param(name, self.values[key], section)

    @staticmethod
    def _base(key):
        return INPUTS[key][0].split(' [')[0]

    def m(self, key):
        name = INPUTS[key][0]
        if name.endswith('[ft]'):
            k = FT
        elif name.endswith('[in]'):
            k = IN
        else:
            raise ValueError(name + ' is not a length')
        return (self.raw(key) * k).named(self._base(key) + ' [m]', S_DIM)

    def rad(self, key):
        assert INPUTS[key][0].endswith('[deg]'), key
        return (self.raw(key) * DEG).named(self._base(key) + ' [rad]', S_DIM)

    def tan(self, key):
        return fl.tan(self.rad(key)).named('Tangent of ' + self._base(key)[0].lower() + self._base(key)[1:], S_DIM)

    def sin(self, key):
        return fl.sin(self.rad(key)).named('Sine of ' + self._base(key)[0].lower() + self._base(key)[1:], S_DIM)

    def cos(self, key):
        return fl.cos(self.rad(key)).named('Cosine of ' + self._base(key)[0].lower() + self._base(key)[1:], S_DIM)

    def frac(self, key):
        assert '[%' in INPUTS[key][0], key
        return self.raw(key) * 0.01

    def station(self, key):
        assert INPUTS[key][0].endswith('[% length]'), key
        return (self.raw(key) * 0.01 * self.m('length')).named(self._base(key) + ' [m]', S_DIM)

    # plain numbers for bounding boxes, checks and analysis
    def num(self, node):
        return fl.num(node)


def table():
    """The inputs as rows for documentation: name, value, section, description."""
    return [(v[0], v[1], v[2], v[3]) for v in INPUTS.values()]
