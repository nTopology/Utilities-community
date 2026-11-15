"""Shape helpers built on fieldlab. Every result is a field in meters, negative inside."""
from __future__ import annotations

import math

import numpy as np

from fieldlab import (F, X, Y, Z, Guide, absf, clamp, const, cos, fmax, fmin, length2, length3, lift, mix, powf,
                      saturate, sin, smax, smin, smoothstep, sqrt, subtract, union, intersect)

_gcount = [0]


def G(name, xs, vs, n=None):
    """Fair guide through station values.

    A shape-preserving (PCHIP) curve through the stations is sampled densely and
    approximated by a clamped uniform cubic B-spline, so the guide does not
    overshoot between stations.
    """
    from scipy.interpolate import PchipInterpolator
    xs, vs = np.asarray(xs, float), np.asarray(vs, float)
    dense = np.linspace(xs[0], xs[-1], 12 * len(xs))
    n = n or max(6, int(round(1.6 * len(xs))))
    return Guide.through(name, dense, PchipInterpolator(xs, vs)(dense), n=n)


def gconst(v):
    return lambda u: const(v)


# --------------------------------------------------------------------------
# frames
# --------------------------------------------------------------------------
class Frame:
    """Orthonormal local frame: u, v, w are local coordinates of a world point."""

    def __init__(self, origin, eu, ev, ew=None, coords=None):
        self.coords = coords or (X, Y, Z)
        o = np.array(origin, float)
        eu = np.array(eu, float)
        eu /= np.linalg.norm(eu)
        ev = np.array(ev, float)
        ev = ev - eu * (ev @ eu)
        ev /= np.linalg.norm(ev)
        ew = np.cross(eu, ev) if ew is None else np.array(ew, float)
        self.o, self.eu, self.ev, self.ew = o, eu, ev, ew
        self.u = self._dot(eu)
        self.v = self._dot(ev)
        self.w = self._dot(ew)

    def _dot(self, e):
        o = self.o
        out = const(-float(o @ e))
        for c, k in zip(self.coords, e):
            if abs(k) > 1e-12:
                out = out + c * float(k)
        return out

    def world(self, u, v, w):
        return self.o + self.eu * u + self.ev * v + self.ew * w


def rot2(a, b, deg):
    """Rotate the coordinate pair (a, b) by an angle in degrees."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return a * c + b * s, b * c - a * s


# --------------------------------------------------------------------------
# 2D profile fields
# --------------------------------------------------------------------------
def rrect2(a, b, ha, hb, r):
    """Rounded rectangle SDF in coordinates (a, b), half sizes ha, hb, corner radius r."""
    qa = absf(a) - (lift(ha) - r)
    qb = absf(b) - (lift(hb) - r)
    return length2(fmax(qa, 0.0), fmax(qb, 0.0)) + fmin(fmax(qa, qb), 0.0) - r


def ellipse2(a, b, ra, rb):
    """Approximate ellipse distance."""
    n = length2(a / ra, b / rb)
    s = min(ra, rb) if not isinstance(ra, F) and not isinstance(rb, F) else fmin(ra, rb)
    return (n - 1.0) * s


def superellipse_norm(a, b, p):
    """(|a|^p + |b|^p)^(1/p) for a, b >= 0. p may be a float or a field."""
    if not isinstance(p, F):
        if p == 2:
            return length2(a, b)
        if p == 4:
            return sqrt(sqrt(a ** 4 + b ** 4))
    # Factor out the larger term first. The power sum is then at least 1, so the base
    # clamp inside powf never acts on it. Without this the clamp put a floor under the
    # norm near a = 0, b = 0 and left a hairline groove along every loft crown line.
    m = fmax(a, b) + 1e-12
    return m * powf(powf(a / m, p) + powf(b / m, p), 1.0 / p)


def section_field(y, z, w, zt, zb, zw, pt, pb, yc=0.0):
    """Asymmetric superelliptic section. w half width, zt top, zb bottom, zw widest height.

    Returns an approximate distance: negative inside the section.
    """
    a = absf(y - yc) / w
    hu = zt - zw
    hd = zw - zb
    bu = fmax((z - zw) / hu, 0.0)
    bd = fmax((zw - z) / hd, 0.0)
    n = superellipse_norm(a, bu, pt) + superellipse_norm(a, bd, pb) - a
    h = (hu + hd) * 0.5
    s = (w * h) / (w + h)
    return (n - 1.0) * s * 1.6


def end_cap(x, x_tip, length, toward=1.0):
    """Elliptic closure factor: 0 at the tip, 1 after `length`. toward=+1: tip at low x."""
    t = saturate((x - x_tip) * (toward / length))
    return sqrt(fmax(t * (2.0 - t), 1e-6))


# --------------------------------------------------------------------------
# airfoils
# --------------------------------------------------------------------------
NACA = (0.2969, -0.1260, -0.3516, 0.2843, -0.1015)


def foil_section(xl, zl, chord, thick, camber, te=0.0018):
    """Cambered airfoil in local chord coordinates.

    xl: distance aft of the leading edge along the chord line (m)
    zl: distance above the chord line (m), chord: local chord (m)
    thick: max thickness / chord, camber: max camber / chord (positive = bulges down)
    The squared-thickness form keeps the leading edge smooth.
    """
    u = xl / chord
    uc = saturate(u)
    su = sqrt(uc)
    a0, a1, a2, a3, a4 = NACA
    # half thickness / chord for unit thickness ratio 0.2
    yt = (a0 * su + uc * (a1 + uc * (a2 + uc * (a3 + uc * a4))))
    tc = 5.0 * lift(thick)
    half = yt * tc * chord + te / 2
    zc = uc * (1.0 - uc) * (-4.0) * lift(camber) * chord
    v = zl - zc
    # linear extension of half^2 ahead of the leading edge keeps the nose round
    lead = fmin(u, 0.0) * chord * (a0 * a0) * tc * tc * chord
    P = half * half + lead
    eps = (a0 * a0) * tc * tc * chord * 0.5
    f = (v * v - P) / (absf(v) + sqrt(fmax(P, 0.0)) + eps)
    return fmax(f, (u - 1.0) * chord)


def wing_element(span_coord, x, z, x_le, z_le, chord, incidence_deg, thick, camber, te=0.0018):
    """Wing element with spanwise guides. incidence positive = trailing edge up (downforce)."""
    th = lift(incidence_deg) * (math.pi / 180.0)
    c, s = cos(th), sin(th)
    dx = x - x_le
    dz = z - z_le
    xl = dx * c + dz * s
    zl = dz * c - dx * s
    return foil_section(xl, zl, chord, thick, camber, te)


# --------------------------------------------------------------------------
# links, tubes, revolved profiles
# --------------------------------------------------------------------------
def blade_link(p, q, half_chord, half_thick, up=(0, 0, 1), round_ends=True, coords=None):
    """Flattened aero-section link from p to q (ellipse section, chord roughly fore-aft)."""
    p, q = np.array(p, float), np.array(q, float)
    L = float(np.linalg.norm(q - p))
    fr = Frame(p, q - p, np.cross(np.array(up, float), q - p), coords=coords)
    # fr.u along the link, fr.v across (chordwise), fr.w thickness direction
    t = clamp(fr.u, 0.0, L)
    du = fr.u - t
    n = length3(du / half_thick, fr.v / half_chord, fr.w / half_thick) if round_ends else length2(fr.v / half_chord, fr.w / half_thick)
    f = (n - 1.0) * half_thick
    if not round_ends:
        f = fmax(f, -fr.u, fr.u - L)
    return f


def tube_from_surfaces(d1, d2, r):
    """Tube around the intersection curve of two surfaces with distance-like fields."""
    return length2(d1, d2) - r


def revolve_coords(frame: Frame):
    """Axial and radial coordinates around frame.u."""
    return frame.u, length2(frame.v, frame.w)


def rod(p, q, r, coords=None):
    """Round rod (capsule) from p to q in the given coordinate triple."""
    p, q = np.array(p, float), np.array(q, float)
    L = float(np.linalg.norm(q - p))
    ref = np.array([0, 0, 1.0]) if abs((q - p)[2]) < 0.9 * L else np.array([1.0, 0, 0])
    fr = Frame(p, q - p, np.cross(ref, q - p), coords=coords)
    t = clamp(fr.u, 0.0, L)
    return length3(fr.u - t, fr.v, fr.w) - r


def ellipsoid(c, r, coords=None):
    cx, cy, cz = coords or (X, Y, Z)
    n = length3((cx - c[0]) / r[0], (cy - c[1]) / r[1], (cz - c[2]) / r[2])
    return (n - 1.0) * min(r)


def rbox(c, half, r, coords=None):
    """Rounded box centred at c with half sizes and edge radius r."""
    cx, cy, cz = coords or (X, Y, Z)
    qx = absf(cx - c[0]) - (half[0] - r)
    qy = absf(cy - c[1]) - (half[1] - r)
    qz = absf(cz - c[2]) - (half[2] - r)
    return length3(fmax(qx, 0.0), fmax(qy, 0.0), fmax(qz, 0.0)) + fmin(fmax(qx, qy, qz), 0.0) - r
