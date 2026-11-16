"""Planar regions and lines for feature outlines, as native Spline DF curves.

A region is a closed cubic Spline DF in a view plane (side: X-Z, front or rear: |Y|-Z,
plan: X-|Y|), extruded through the car. It is negative inside. Corners are rounded by a
chosen amount; the straight runs between corners stay exactly straight.
"""
from __future__ import annotations

import numpy as np

from fieldlab import *


def rounded_polygon(pts, r, max_gap=0.22):
    """Control points of a closed cubic B-spline that follows the polygon with rounded corners.

    Every corner contributes three control points: one on each edge at distance r (or less on
    short edges) and the corner itself. Four collinear points in a row make the middle of each
    edge exactly straight. The loop starts and ends at an edge midpoint, so the clamped ends
    of the Spline DF meet without a kink."""
    P = np.asarray(pts, float)
    if np.linalg.norm(P[0] - P[-1]) < 1e-9:
        P = P[:-1]
    # clockwise in a right-handed (u, v) plane puts the inside on the right: negative inside
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area > 0:
        P = P[::-1]
    n = len(P)
    rr = np.broadcast_to(np.asarray(r, float), (n,)) if np.ndim(r) else np.full(n, float(r))
    if area > 0 and np.ndim(r):
        rr = rr[::-1]
    out = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        la, lc = np.linalg.norm(a - b), np.linalg.norm(c - b)
        ra, rc = min(rr[i], 0.45 * la), min(rr[i], 0.45 * lc)
        out += [b + (a - b) / la * ra, b, b + (c - b) / lc * rc]
    # long edges get extra collinear points, so the parameter speed stays even along the loop
    full = []
    for i in range(n):
        full += out[3 * i:3 * i + 3]
        p0, p1 = out[3 * i + 2], out[(3 * i + 3) % len(out)]
        m = int(np.linalg.norm(p1 - p0) // max_gap)
        full += [p0 + (p1 - p0) * (j + 1) / (m + 1) for j in range(m)]
    out = np.array(full)
    return _close_on_longest(out)


def _close_on_longest(out):
    """Start and end the loop at the midpoint of its longest leg (which is straight)."""
    seg = np.linalg.norm(np.roll(out, -1, axis=0) - out, axis=1)
    k = int(np.argmax(seg))
    out = np.roll(out, -(k + 1), axis=0)
    mid = 0.5 * (out[0] + out[-1])
    return np.vstack([mid, out, mid])


def region(label, pts, u, v, r=0.02):
    """Closed region from polygon vertices (u, v). Negative inside."""
    cps = [(const(float(a)), const(float(b))) for a, b in rounded_polygon(pts, r)]
    return spline2d(cps, u, v, label=label)


def curve(label, pts, u, v):
    """Unsigned distance to an open cubic Spline DF curve through control points (u, v).
    The curve continues past both ends along its end tangents."""
    cps = [(const(float(a)), const(float(b))) for a, b in pts]
    return absf(spline2d(cps, u, v, label=label))


def interp_ctrl(pts, n=None):
    """Control points whose clamped cubic B-spline passes close to the given polyline: the
    polyline is resampled and fitted by least squares, so the curve follows it rather than
    cutting its corners."""
    from scipy.interpolate import BSpline
    P = np.asarray(pts, float)
    n = n or max(4, len(P))
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    t = np.linspace(0, d[-1], 200)
    Q = np.c_[np.interp(t, d, P[:, 0]), np.interp(t, d, P[:, 1])]
    knots = np.r_[np.zeros(4), np.arange(1, n - 3) / (n - 3), np.ones(4)]
    A = BSpline.design_matrix(np.clip(t / d[-1], 0, 1 - 1e-12), knots, 3).toarray()
    c = np.linalg.lstsq(A, Q, rcond=None)[0]
    c[0], c[-1] = P[0], P[-1]
    return c
