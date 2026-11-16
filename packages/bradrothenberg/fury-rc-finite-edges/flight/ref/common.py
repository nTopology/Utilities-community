"""Shared constants, units and the standard atmosphere of the point-performance routines. Numpy only.

Stored values are SI. Everything shown to a person is converted to US customary units and then rounded.
"""
from __future__ import annotations
import math
import numpy as np

G0 = 9.80665
FT, IN, FT2 = 0.3048, 0.0254, 0.09290304
LB, LBF = 0.45359237, 4.4482216152605
KT, NMI = 0.514444, 1852.0
PSF = LBF / FT2                    # Pa per lb/ft2
SLUG_FT2 = 1.3558179483            # kg m2 per slug ft2
GAL = 0.003785411784               # m3 per US gallon
GAMMA, R_AIR = 1.4, 287.053


def isa(h_m):
    """1976 standard atmosphere to 20 km. h in metres (geopotential). Returns a dict of SI values."""
    T0, p0 = 288.15, 101325.0
    if h_m <= 11000.0:
        T = T0 - 0.0065 * h_m
        p = p0 * (T / T0) ** 5.25588
    else:
        T = 216.65
        p = 22632.06 * math.exp(-(h_m - 11000.0) / 6341.62)
    rho = p / (R_AIR * T)
    return dict(T=T, p=p, rho=rho, a=math.sqrt(GAMMA * R_AIR * T), mu=1.458e-6 * T ** 1.5 / (T + 110.4),
                p_ratio=p / p0, t_ratio=T / T0, sigma=rho / 1.225)


def r3(v, n=3):
    """Round floats inside nested lists/dicts for JSON."""
    if isinstance(v, dict):
        return {k: r3(x, n) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)):
        return [r3(x, n) for x in v]
    if isinstance(v, (float, np.floating)):
        return round(float(v), n)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def us(**kw):
    """Display block in US customary units from SI keyword values: us(span_m=..., area_m2=..., mass_kg=...)."""
    out = {}
    for k, v in kw.items():
        if v is None:
            continue
        if k.endswith('_kg_m2'):
            out[k[:-6] + '_lb_ft2'] = round(v * G0 / PSF, 1)
        elif k.endswith('_m2'):
            out[k[:-3] + '_ft2'] = round(v / FT2, 1)
        elif k.endswith('_kgm2'):
            out[k[:-5] + '_slug_ft2'] = round(v / SLUG_FT2)
        elif k.endswith('_kg'):
            out[k[:-3] + '_lb'] = round(v / LB)
        elif k.endswith('_N'):
            out[k[:-2] + '_lbf'] = round(v / LBF)
        elif k.endswith('_m3'):
            out[k[:-3] + '_gal'] = round(v / GAL, 1)
        elif k.endswith('_small_m'):
            out[k[:-8] + '_in'] = round(v / IN, 1)
        elif k.endswith('_m_s'):
            out[k[:-4] + '_kt'] = round(v / KT, 1)
        elif k.endswith('_m'):
            out[k[:-2] + '_ft'] = round(v / FT, 2)
        else:
            out[k] = v
    return out
