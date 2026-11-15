"""External fittings of the Fury model: the small things on the outside that the photographs show.

  Wing pylons and launch rails   one pylon with a rail launcher under each wing (photographs 06, 07, 08, 23)
  Missiles                       a plain shape of the size of an AIM-120 on each rail (a dummy: body, nose, fins)
  Flap actuator fairings         the teardrop fairing under each wing on the flap hinge line (photograph 01)
  Dorsal scoop                   the small ram air scoop on the spine (photographs 12, 23, 25)
  Antennas and probes            blade antennas on the spine and the belly, an air data probe on each side of the nose

Positions are read from the photographs as fractions of the length and of the span. They are estimates: good to
a few inches, not surveyed. The input "Wing stores" set to 0 removes the pylons, rails and missiles (clean wing,
as in photograph 01).
"""
from __future__ import annotations

import math

import fieldlab as fl
from fieldlab import X, Y, Z, absf, clamp, fmax, fmin, length2, length3
from shapes import rbox
from oml import AY, BIG, BELLY, CROWN, CHINE, HALF_WIDTH, LREF
from gear import rod, ball

S_FIT = '33 External fittings'
IN = 0.0254

STORE_SPAN = 56.0            # pylon centre from the centreline [in at the reference size]
RAIL = dict(ahead=18.5, length=82.0, half_width=1.75, half_height=2.6, drop=7.4)    # rail launcher [in]; ahead of the wing leading edge
PYLON = dict(front=10.0, aft=52.0, half_width=0.9)                                    # [in] aft of the wing leading edge
MISSILE = dict(length=144.0, radius=3.5, nose=22.0, ahead=30.0, fin_span=17.5)      # AIM-120 size [in]
FAIRING = dict(span=0.68, chord=0.74, half_length=10.0, half_width=2.0, depth=2.4)  # flap actuator fairing
SCOOP = dict(station=0.405, half_length=7.5, half_width=3.3, height=2.7)            # dorsal scoop [in]
BLADES_TOP = [0.47, 0.52]                                                           # blade antennas on the spine
BLADES_BELLY = [0.65, 0.775]                                                        # blade antennas on the belly
PROBE_STATION = 0.146                                                               # air data probes


class Fittings:
    def __init__(self, model):
        self.model = model
        d, af = model.d, model.af
        self.d, self.af = d, af
        self.s = af.scale
        self.ws = (af.scale * d.raw('width_scale')).named('Breadth scale of the fittings', S_FIT)
        self.hs = (af.scale * d.raw('height_scale')).named('Height scale of the fittings', S_FIT)
        self.stores_off = ((1.0 - d.raw('wing_stores')) * BIG).named('Wing stores removed when > 0', S_FIT)
        self.crown_z = (CROWN(af.xr) * self.hs).named('Crown height at this station [m]', S_FIT)
        self.belly_z = (BELLY(af.xr) * self.hs).named('Belly height at this station [m]', S_FIT)

    # ------------------------------------------------------------------ wing stores
    def _store_frame(self):
        """Where the pylon hangs: its span position, the wing leading edge there, and the chord plane height."""
        d = self.d
        yp = (self.s * (STORE_SPAN * IN)).named('Pylon centre from the centreline [m]', S_FIT)
        x_le = (d.station('wing_apex') + yp * d.tan('wing_sweep')).named('Wing leading edge at the pylon [m]', S_FIT)
        z0 = (d.m('wing_height') + yp * d.tan('wing_dihedral')).named('Wing chord plane at the pylon [m]', S_FIT)
        return yp, x_le, z0

    def pylons(self):
        yp, x_le, z0 = self._store_frame()
        s = self.s
        below = z0 - Z                                               # distance below the wing chord plane
        pylon = fmax(absf(AY - yp) - PYLON['half_width'] * IN, x_le + s * (PYLON['front'] * IN) - below * 0.9 - X,
                     X - x_le - s * (PYLON['aft'] * IN), -below, below - (RAIL['drop'] - RAIL['half_height'] + 0.5) * IN)
        x_c = x_le + s * ((RAIL['length'] * 0.5 - RAIL['ahead']) * IN)
        rail = rbox((x_c, yp, z0 - RAIL['drop'] * IN), (s * (RAIL['length'] * 0.5 * IN), RAIL['half_width'] * IN, RAIL['half_height'] * IN), 0.7 * IN,
                    coords=(X, AY, Z))
        return (fmin(pylon, rail) + self.stores_off).named('Wing pylons and launch rails', S_FIT)

    def missiles(self):
        yp, x_le, z0 = self._store_frame()
        s, M = self.s, MISSILE
        R = M['radius'] * IN
        x_nose = x_le - s * ((RAIL['ahead'] + M['ahead']) * IN)
        dy, dz = AY - yp, Z - (z0 - (RAIL['drop'] + RAIL['half_height'] + 0.6 + M['radius']) * IN)
        rho = length2(dy, dz)
        u = X - x_nose                                               # distance aft of the nose tip
        body = fmax((length2(rho / R, fmax(M['nose'] * IN - u, 0.0) / (M['nose'] * IN)) - 1.0) * R, u - M['length'] * IN)
        # four wings and four fins in an X: plates in the two diagonal planes
        k = math.sqrt(0.5)
        a, b = absf(dy + dz) * k, absf(dy - dz) * k
        reach = fmax(a, b)                                           # distance out along a fin
        plate = fmin(a, b) - 0.15 * IN
        half = M['fin_span'] * 0.5 * IN

        def fins(x0, x1, sweep):
            return fmax(plate, reach - half, u - x1 * IN, x0 * IN + (reach - R) * sweep - u)
        return (fmin(body, fins(66.0, 84.0, 1.3), fins(128.0, 143.0, 0.9)) + self.stores_off).named('Missiles', S_FIT)

    # ------------------------------------------------------------------ wing
    def flap_fairings(self):
        p = self.af.panels['Wing']
        F = FAIRING
        u = X - p['x_le'] - p['chord'] * F['chord']
        across = p['s'] - p['length'] * F['span']
        n = p['n'] + 1.0 * IN                                        # centred just under the chord plane
        f = (length3(u / (F['half_length'] * IN), across / (F['half_width'] * IN), n / (F['depth'] * IN)) - 1.0) * (F['half_width'] * IN)
        return fmax(f, p['n']).named('Flap actuator fairings', S_FIT)

    # ------------------------------------------------------------------ fuselage
    def scoop(self):
        """A half-buried rounded bump on the spine, open to the front."""
        S = SCOOP
        u = X - self.af.L * S['station']
        up = Z - self.crown_z

        def bump(grow):
            return (length3(u / ((S['half_length'] + grow) * IN), Y / ((S['half_width'] + grow) * IN), up / ((S['height'] + grow) * IN)) - 1.0) * ((S['height'] + grow) * IN)
        mouth = -u - 0.55 * S['half_length'] * IN                    # cut the front off, so the scoop has a mouth
        hollow = fmax(bump(-0.45), u - 0.25 * S['half_length'] * IN)
        return fmax(bump(0.0), mouth, -hollow, -up - 0.03).named('Dorsal scoop', S_FIT)

    def _blade(self, station, surface_z, up_sign):
        """A swept blade antenna standing on the centreline: 6 in tall, 6 in chord at the root."""
        u = X - self.af.L * station
        h = (Z - surface_z) * up_sign                                # height above the skin (below it on the belly)
        return fmax(absf(Y) - 0.3 * IN, -h - 1.0 * IN, h - 6.0 * IN, h * 0.8 - u, u - 6.0 * IN - h * 0.25)

    def antennas(self):
        blades = [self._blade(t, self.crown_z, 1.0) for t in BLADES_TOP] + [self._blade(t, self.belly_z, -1.0) for t in BLADES_BELLY]
        # air data probes: a stub out of each side of the nose under the chine, then a tube pointing forward
        x = self.af.L * PROBE_STATION
        half = self.ws * float(HALF_WIDTH.value(PROBE_STATION * LREF))
        zc = self.hs * float(CHINE.value(PROBE_STATION * LREF))
        c = (X, AY, Z)
        root, elbow = (x, half * 0.7, zc - 1.2 * IN), (x, half + 3.2 * IN, zc - 2.2 * IN)
        tip = (x - 5.5 * IN, half + 3.2 * IN, zc - 2.2 * IN)
        probe = fmin(rod(root, elbow, 0.45 * IN, c), rod(elbow, tip, 0.32 * IN, c), ball(elbow, 0.5 * IN, c))
        return fmin(probe, *blades).named('Antennas and probes', S_FIT)

    # ------------------------------------------------------------------ bodies
    def bodies(self):
        """(name, field, material, bounding box name, mesh size)."""
        return [('Wing pylons and launch rails', self.pylons(), 'skin_b', 'wing', 0.003),
                ('Missiles', self.missiles(), 'antenna', 'stores', 0.003),
                ('Flap actuator fairings', self.flap_fairings(), 'skin_b', 'wing', 0.003),
                ('Dorsal scoop', self.scoop(), 'skin_b', 'fuselage', 0.0025),
                ('Antennas and probes', self.antennas(), 'composite', 'fuselage', 0.002)]

    def stores_box(self):
        d = self.d
        L = d.value('length') * 0.3048
        y = STORE_SPAN * IN * L / LREF
        x0 = d.value('wing_apex') * 0.01 * L + y * math.tan(math.radians(d.value('wing_sweep')))
        z = d.value('wing_height') * IN
        return ([x0 - 1.5, -y - 0.35, z - 0.75], [x0 + 3.2, y + 0.35, z + 0.1])
