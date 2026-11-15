"""Cross sections of the fuselage at a list of stations (fractions of the length). sections.py <out png> [t ...]"""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))
import fieldlab as fl, registry
from design import Design
from oml import Airframe
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ts = [float(a) for a in sys.argv[2:]] or [0.15, 0.27, 0.30, 0.33, 0.36, 0.40, 0.45, 0.52, 0.60, 0.68, 0.74, 0.90]
af = Airframe(Design())
L = fl.num(af.L)
body, air = af.fuselage(True), af.duct_air()
h = 0.003
y = np.arange(-0.09 * L, 0.09 * L, h)
z = np.arange(-0.06 * L, 0.09 * L, h)
Y, Z = np.meshgrid(y, z, indexing='ij')
n = len(ts)
cols = 4
fig, axs = plt.subplots((n + cols - 1) // cols, cols, figsize=(4 * cols, 3.4 * ((n + cols - 1) // cols)))
for ax, t in zip(axs.ravel(), ts):
    pts = np.c_[np.full(Y.size, t * L), Y.ravel(), Z.ravel()]
    b = registry.values_at(body, pts).reshape(Y.shape)
    a = registry.values_at(air, pts).reshape(Y.shape)
    ax.contourf(Y / 0.0254, Z / 0.0254, b, levels=[-1e9, 0], colors=['#9aa3ad'])
    ax.contourf(Y / 0.0254, Z / 0.0254, a, levels=[-1e9, 0], colors=['#cfe6f7'])
    ax.contour(Y / 0.0254, Z / 0.0254, b, levels=[0], colors='k', linewidths=0.8)
    ax.set_aspect('equal')
    ax.set_title(f'station {t * 100:.0f} % of length ({t * L / 0.3048:.1f} ft)', fontsize=9)
    ax.tick_params(labelsize=7)
for ax in axs.ravel()[n:]:
    ax.axis('off')
fig.suptitle('Fuselage cross sections: structure envelope (grey), inlet duct air (blue). Inches.', fontsize=11)
fig.tight_layout()
fig.savefig(sys.argv[1], dpi=110)
