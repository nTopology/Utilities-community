"""
X-59 quick aero check -- called from the "Run Aero Analysis" block in the nTop notebook.

nTop builds a command line like
    python "C:/path/to/x59_aero.py" wing_span=9000 wing_root_chord=13210 ... cg_x=17000
and shows whatever this script prints in the "Aero Results" text block.

Lengths come in as millimetres and angles as degrees, matching the notebook.
Any parameter not passed on the command line falls back to DEFAULTS below, so
`python x59_aero.py` on its own analyses the baseline aircraft.

Uses AeroSandbox's AeroBuildup (semi-empirical, includes compressibility and wave
drag). Expect trends you can trust and absolute numbers within ~10-20%.
"""
import os
import subprocess
import sys

# ----------------------------------------------------------------------------
# Baseline values (copied from the X-59 notebook). mm / deg / kg / m.
# ----------------------------------------------------------------------------
DEFAULTS = {
    # Main wing (full span, quarter-chord sweeps, double-trapezoid planform)
    "wing_x": 12220, "wing_z": 350,
    "wing_root_chord": 13210, "wing_span": 9000,
    "wing_inner_sweep": 68.3, "wing_inner_taper": 0.2105,
    "wing_outer_sweep": 60.8, "wing_outer_taper": 0.4,
    "wing_break": 0.804, "wing_dihedral": 0, "wing_incidence": 2,
    # Twist at root, panel break and tip, linear in between (negative = washout)
    "wing_root_twist": 0, "wing_break_twist": -2.412, "wing_tip_twist": -3,
    "wing_naca": "0003",
    # Canards
    "canard_x": 10780, "canard_z": 660,
    "canard_root_chord": 2030, "canard_span": 2270,
    "canard_sweep": 54.8, "canard_taper": 0.46,
    "canard_twist": 8, "canard_dihedral": 5, "canard_incidence": 4,
    "canard_naca": "0004",
    # Horizontal stabilizer (root point = root leading edge)
    "hstab_x": 25280, "hstab_z": 450,
    "hstab_root_chord": 4810, "hstab_span": 4490,
    "hstab_sweep": 57.4, "hstab_taper": 0.116,
    # Points along the notebook's Top / Side / Bottom Rail splines (comma-separated, mm),
    # sampled by the Aero Fuselage Points count. Side rail y is the half-width.
    # These defaults are the rails' control points, close enough for a standalone run.
    "fuse_top_x": "0,1118.3,3361.2,6710.3,10065.5,13390.6,16761.1,20113.4,23471.2,26838.8,29086.8,30191.3",
    "fuse_top_z": "30,104.8,206.3,559.3,824.9,1426.6,1350.7,1025.1,782.1,777.4,775.4,556.5",
    "fuse_side_x": "0,1069.1,3329.3,6680.3,10043.1,13398.4,16761.2,20122.5,23482.9,26848.9,29078.6,30191.3",
    "fuse_side_y": "30,367.5,316.1,422.5,557.5,583.9,568.8,576.1,573.6,576,619.5,521.7",
    "fuse_bot_x": "0,1110.9,3353.5,6713.7,10074.7,13436.5,16796.3,20160.3,23514.4,26887.3,29096.9,30191.3",
    "fuse_bot_z": "-30,-197.9,-210.9,-271.3,-302.5,-323.7,-299.7,-315.7,-108.5,-292.3,86.3,347.8",
    # Flight condition / mass properties
    "mach": 1.41,           # X-59 design cruise (~1.4)
    "altitude": 16760,      # m (55,000 ft)
    "mass": 14660,          # kg, notebook mass statement total (full fuel)
    "cg_x": 18269,          # mm from the nose, from the notebook mass statement
    "open_plot": 1,         # 1 = pop the results image open after each run
}

# Fixed parts students are not expected to edit (from the notebook).
VSTAB = dict(x=23680, z=750, root_chord=5450, span=2485, inner_sweep=53.5,
             inner_taper=0.634, outer_sweep=53.5, outer_taper=0.4226, brk=0.5)
TSTAB = dict(x=28170, z=3165, root_chord=1500, span=1390, sweep=35, taper=0.6)


def ensure_aerosandbox():
    try:
        import aerosandbox  # noqa: F401
    except ImportError:
        print("AeroSandbox not found -- installing it (first run only, ~1-2 min)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "aerosandbox"])


def parse_args(argv):
    p = dict(DEFAULTS)
    for arg in argv:
        if "=" not in arg:
            continue
        key, val = arg.split("=", 1)
        key = key.strip().lower()
        if key not in DEFAULTS:
            print(f"WARNING: unknown parameter '{key}' ignored")
            continue
        p[key] = val.strip() if isinstance(DEFAULTS[key], str) else float(val)
    return p


def fuselage_stations(p):
    """Fuselage stations (x, half-width, z_top, z_bottom) in mm at the top rail's point
    x positions, with the side and bottom rails interpolated onto them."""
    import numpy as onp
    rail = {}
    for name in ("top", "side", "bot"):
        xs = [float(v) for v in str(p[f"fuse_{name}_x"]).split(",")]
        vs = [float(v) for v in str(p[f"fuse_{name}_{'y' if name == 'side' else 'z'}"]).split(",")]
        if len(xs) != len(vs):
            raise ValueError(f"fuselage {name} rail has {len(xs)} x values but {len(vs)} others")
        rail[name] = (onp.array(xs), onp.array(vs))
    x, z_top = rail["top"]
    half_width = onp.interp(x, *rail["side"])
    z_bot = onp.interp(x, *rail["bot"])
    return list(zip(x, half_width, z_top, z_bot))


def naca(code):
    import aerosandbox as asb
    code = str(code).strip()
    return asb.Airfoil(f"naca{code.zfill(4)}")


def lifting_surface(asb, name, x, z, root_chord, span, panels, airfoil, incidence=0.0,
                    twist=0.0, dihedral=0.0, symmetric=True, vertical=False, color=None,
                    station_twists=None):
    """Build a wing from a root LE point and a list of (span_fraction, chord, qc_sweep_deg) panels.
    Twist is applied as washout reaching -twist/2 at the tip (matches the nTop wing block notes),
    unless station_twists gives the twist at the root and at each panel end directly
    (matches the Twisted 2 Panel Wing block). All inputs in mm/deg; returns an asb.Wing in metres."""
    import aerosandbox.numpy as np
    m = 1e-3
    half = span / 2 if symmetric else span
    xsecs = []
    x_qc, s, c = x + 0.25 * root_chord, 0.0, root_chord
    stations = [(0.0, root_chord, 0.0)]
    for frac, chord, sweep in panels:
        ds = (frac * half) - s
        x_qc += ds * np.tand(sweep)
        s = frac * half
        stations.append((s, chord, x_qc))
    for i, (s, chord, xq) in enumerate(stations):
        xle = x if i == 0 else xq - 0.25 * chord
        if station_twists is not None:
            tw = incidence + station_twists[i]
        else:
            tw = incidence - (twist / 2) * (s / half)
        off = s * np.tand(dihedral)
        xyz = [xle * m, 0, (z + s) * m] if vertical else [xle * m, s * m, (z + off) * m]
        xsecs.append(asb.WingXSec(xyz_le=xyz, chord=chord * m, twist=tw, airfoil=airfoil))
    return asb.Wing(name=name, symmetric=symmetric, xsecs=xsecs, color=color)


def build_airplane(p):
    import aerosandbox as asb
    m = 1e-3
    w_brk = p["wing_root_chord"] * p["wing_inner_taper"]
    wing = lifting_surface(
        asb, "Main Wing", p["wing_x"], p["wing_z"], p["wing_root_chord"], p["wing_span"],
        [(p["wing_break"], w_brk, p["wing_inner_sweep"]),
         (1.0, w_brk * p["wing_outer_taper"], p["wing_outer_sweep"])],
        naca(p["wing_naca"]), p["wing_incidence"], dihedral=p["wing_dihedral"],
        station_twists=[p["wing_root_twist"], p["wing_break_twist"], p["wing_tip_twist"]])
    canard = lifting_surface(
        asb, "Canards", p["canard_x"], p["canard_z"], p["canard_root_chord"], p["canard_span"],
        [(1.0, p["canard_root_chord"] * p["canard_taper"], p["canard_sweep"])],
        naca(p["canard_naca"]), p["canard_incidence"], p["canard_twist"], p["canard_dihedral"])
    hstab = lifting_surface(
        asb, "H-Stab", p["hstab_x"], p["hstab_z"], p["hstab_root_chord"], p["hstab_span"],
        [(1.0, p["hstab_root_chord"] * p["hstab_taper"], p["hstab_sweep"])], naca("0004"))
    v = VSTAB
    v_brk = v["root_chord"] * v["inner_taper"]
    vstab = lifting_surface(
        asb, "V-Stab", v["x"], v["z"], v["root_chord"], v["span"],
        [(v["brk"], v_brk, v["inner_sweep"]), (1.0, v_brk * v["outer_taper"], v["outer_sweep"])],
        naca("0004"), symmetric=False, vertical=True)
    t = TSTAB
    tstab = lifting_surface(
        asb, "T-Tail", t["x"], t["z"], t["root_chord"], t["span"],
        [(1.0, t["root_chord"] * t["taper"], t["sweep"])], naca("0004"))
    fuse = asb.Fuselage(name="Fuselage", xsecs=[
        asb.FuselageXSec(xyz_c=[x * m, 0, (zt + zb) / 2 * m],
                         width=2 * hw * m, height=max(zt - zb, 1) * m, shape=2.5)
        for x, hw, zt, zb in fuselage_stations(p)])
    return asb.Airplane(name="X-59 (student variant)", xyz_ref=[p["cg_x"] * m, 0, 0],
                        wings=[wing, canard, hstab, vstab, tstab], fuselages=[fuse])


def main():
    ensure_aerosandbox()
    import aerosandbox as asb
    import aerosandbox.numpy as np

    p = parse_args(sys.argv[1:])
    plane = build_airplane(p)
    wing = plane.wings[0]
    S, mac = wing.area(), wing.mean_aerodynamic_chord()

    atmo = asb.Atmosphere(altitude=p["altitude"])
    V = p["mach"] * atmo.speed_of_sound()

    # Angle-of-attack sweep at the cruise condition
    alpha = np.linspace(-2, 10, 25)
    op = asb.OperatingPoint(atmosphere=atmo, velocity=V, alpha=alpha)
    aero = asb.AeroBuildup(plane, op, xyz_ref=plane.xyz_ref).run()
    CL, CD, Cm = aero["CL"], aero["CD"], aero["Cm"]
    LD = CL / CD

    # Cruise: lift = weight
    q = float(np.atleast_1d(op.dynamic_pressure())[0])
    CL_req = p["mass"] * 9.81 / (q * S)
    a_cr = float(np.interp(CL_req, CL, alpha))
    CD_cr = float(np.interp(a_cr, alpha, CD))
    Cm_cr = float(np.interp(a_cr, alpha, Cm))
    i_ld = int(np.argmax(LD))

    # Neutral point from straight-line fits over the attached-flow part of the sweep:
    # dCm/dCL = -(x_np - x_cg) / c_ref. Fitting is much steadier than point derivatives.
    fit = (alpha >= -1) & (alpha <= 7)
    dCm_dCL = float(np.polyfit(CL[fit], Cm[fit], 1)[0])
    x_np = p["cg_x"] * 1e-3 - dCm_dCL * plane.c_ref
    sm = (x_np - p["cg_x"] * 1e-3) / plane.c_ref
    CLa = float(np.polyfit(alpha[fit], CL[fit], 1)[0])  # per degree

    lines = [
        f"X-59 AERO  |  Mach {p['mach']:.2f} @ {p['altitude'] / 1000:.1f} km  |  mass {p['mass']:.0f} kg",
        f"Wing area {S:.1f} m^2   MAC {mac:.2f} m   span {wing.span():.2f} m   AR {wing.aspect_ratio():.2f}",
        "-- Cruise (lift = weight) --",
        f"  CL needed     {CL_req:.3f}   at alpha {a_cr:.2f} deg",
        f"  CD            {CD_cr:.4f}   ({CD_cr * 1e4:.0f} counts)",
        f"  L/D           {CL_req / CD_cr:.2f}",
        f"  Drag          {CD_cr * q * S / 1000:.1f} kN",
        f"  Cm (about CG) {Cm_cr:+.4f}   ({'nose-up' if Cm_cr > 0 else 'nose-down'}, needs trim)",
        "-- Stability --",
        f"  Neutral point {x_np * 1000:.0f} mm   CG {p['cg_x']:.0f} mm",
        f"  Static margin {sm * 100:+.1f} % MAC   ({'STABLE' if sm > 0 else 'UNSTABLE'})",
        f"  CL_alpha      {CLa:.4f} /deg",
        f"-- Best L/D in sweep: {LD[i_ld]:.2f} at alpha {alpha[i_ld]:.1f} deg --",
    ]
    report = "\n".join(lines)
    print(report)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aero_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "latest_report.txt"), "w") as f:
        f.write(report + "\n\nInputs:\n" + "\n".join(f"  {k} = {v}" for k, v in p.items()))
    png = save_plot(plane, alpha, CL, CD, Cm, LD, a_cr, x_np, report, out_dir)
    print(f"Plot: {png}")
    # Machine-readable line for nTop: the notebook splits the output on "@@" and reads
    # piece 1 = neutral point x (mm from nose), 2 = cruise L/D, 3 = best L/D in the sweep.
    # Add new values at the end so existing indices in the notebook keep working.
    print(f"For nTop (NP mm, cruise L/D, best L/D): "
          f"@@{x_np * 1000:.1f}@@{CL_req / CD_cr:.3f}@@{float(LD[i_ld]):.3f}@@")
    if p["open_plot"] and hasattr(os, "startfile"):
        os.startfile(png)


def save_plot(plane, alpha, CL, CD, Cm, LD, a_cr, x_np, report, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as onp

    fig = plt.figure(figsize=(14, 8))
    ax_top = fig.add_subplot(2, 3, 1)
    ax_side = fig.add_subplot(2, 3, 4)
    for ax, j, title in [(ax_top, 1, "Top view [m]"), (ax_side, 2, "Side view [m]")]:
        for fuse in plane.fuselages:
            xs = onp.array([xs.xyz_c[0] for xs in fuse.xsecs])
            if j == 1:
                half = onp.array([xs.width / 2 for xs in fuse.xsecs])
                lo, hi = -half, half
            else:
                zc = onp.array([xs.xyz_c[2] for xs in fuse.xsecs])
                h = onp.array([xs.height / 2 for xs in fuse.xsecs])
                lo, hi = zc - h, zc + h
            ax.fill_between(xs, lo, hi, color="0.85", ec="0.5")
        for wing in plane.wings:
            le = onp.array([xs.xyz_le for xs in wing.xsecs], dtype=float)
            te = le + onp.array([[xs.chord, 0, 0] for xs in wing.xsecs])
            outline = onp.vstack([le, te[::-1], le[:1]])
            ax.plot(outline[:, 0], outline[:, j], color="tab:blue", lw=1.2)
            if wing.symmetric and j == 1:
                ax.plot(outline[:, 0], -outline[:, 1], color="tab:blue", lw=1.2)
        ax.plot(plane.xyz_ref[0], 0, "r+", ms=14, mew=2, label="CG")
        ax.plot(x_np, 0, "gx", ms=10, mew=2, label="Neutral point")
        ax.set_aspect("equal"); ax.set_title(title); ax.grid(alpha=0.3)
    ax_top.legend(loc="upper left", fontsize=8)

    for k, (y, lab) in enumerate([(CL, "CL"), (CD, "CD"), (LD, "L/D"), (Cm, "Cm (about CG)")]):
        ax = fig.add_subplot(2, 3, [2, 3, 5, 6][k])
        ax.plot(alpha, y, "-o", ms=3)
        ax.axvline(a_cr, color="r", ls="--", lw=1, label="cruise alpha")
        if lab.startswith("Cm"):
            ax.axhline(0, color="k", lw=0.8)
        ax.set_xlabel("alpha [deg]"); ax.set_ylabel(lab); ax.grid(alpha=0.3)
        if k == 0:
            ax.legend()
    fig.suptitle(report.splitlines()[0])
    fig.tight_layout()
    path = os.path.join(out_dir, "latest_results.png")
    fig.savefig(path, dpi=110)
    return path


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # keep the message short so it reads well inside nTop
        print(f"AERO ANALYSIS FAILED: {type(e).__name__}: {e}")
        sys.exit(1)
