# nTop–AVL Aerodynamic Integration

Automate vortex-lattice aerodynamic analysis of a conventional UAV by driving [AVL (Athena Vortex Lattice)](https://web.mit.edu/drela/Public/web/avl/) directly from nTop geometry parameters. The included nTop notebook passes wing, tail, and flight-condition parameters to a Python orchestrator that generates AVL input files, runs the solver, and returns aerodynamic coefficients and stability derivatives back to nTop — all in a single evaluation.

## Prerequisites

- **nTop 4.12+**
- **AVL 3.52** — `avl352.exe` must be on your system `PATH`
- **Python 3.8+** — uses the standard library only (no extra packages required)

## Workflow

1. Open `Cool-1V1.1.2.ntop` in nTop.
2. Set your wing geometry, tail sizing, CG location, and flight condition variables inside the notebook.
3. nTop calls `AVL_prototype.py` as an external process, passing all parameters as command-line arguments.
4. The script generates `Conventional_UAV.avl`, a `.mass` file, and a run-command script, then invokes `avl352.exe`.
5. AVL runs four analyses (base trim, roll, pitch, yaw) and writes `.ft` / `.st` output files.
6. The script parses those files and prints a single CSV line that nTop reads back as output variables.

## Inputs

| Parameter | Description |
|-----------|-------------|
| `wing_area` | Wing reference area (m²) |
| `wing_ar` | Wing aspect ratio |
| `wing_taper` | Wing taper ratio |
| `wing_sweep_c4` | Quarter-chord sweep angle (degrees) |
| `z_wing` | Wing vertical position (m) |
| `aileron_y_start_frac` / `_y_end_frac` | Aileron span extent as fraction of semi-span |
| `aileron_chord_frac` | Aileron chord as fraction of local chord |
| `hstab_area` / `_ar` / `_taper` | Horizontal stabilizer geometry |
| `z_htail` | Horizontal tail vertical position (m) |
| `hstab_incidence` | Horizontal stabilizer incidence angle (degrees) |
| `elevator_y_start_frac` / `_y_end_frac` / `_chord_frac` | Elevator sizing |
| `vstab_area` / `_ar` / `_taper` | Vertical stabilizer geometry |
| `z_vtail` | Vertical tail root height (m) |
| `rudder_z_start_frac` / `_z_end_frac` / `_chord_frac` | Rudder sizing |
| `tail_moment_arm` | Distance from wing LE to tail LE (m) |
| `x_cg` / `y_cg` / `z_cg` | Centre of gravity location (m) |
| `mach` | Freestream Mach number |
| `alpha` | Angle of attack (degrees) |
| `roll_rate` / `pitch_rate` / `yaw_rate` | Body rates (deg/s, optional) |
| `mass` / `ixx` / `iyy` / `izz` | Mass properties (kg, kg·m²) |

## Outputs

| Output | Description |
|--------|-------------|
| `CL` | Lift coefficient |
| `CD` | Drag coefficient |
| `Cm` | Pitching-moment coefficient |
| `Cma` | Pitch-moment-per-alpha derivative (stability) |
| `Cmq` | Pitch-damping derivative |
| `Cnb` | Yaw-moment-per-sideslip derivative |
| `Clb` | Roll-moment-per-sideslip (dihedral effect) |
| `Clp` | Roll-damping derivative |
| `static_margin` | Static margin (% MAC) |
| `elev_trim` | Elevator deflection at trim (degrees) |
| `ail_req` | Aileron deflection for roll maneuver (degrees) |
| `elev_req` | Elevator deflection for pitch maneuver (degrees) |
| `rud_req` | Rudder deflection for yaw maneuver (degrees) |

## Files

| File | Description |
|------|-------------|
| `Cool-1V1.1.2.ntop` | nTop notebook with the full integration workflow |
| `AVL_prototype.py` | Python orchestrator — generates AVL inputs, runs AVL, parses outputs |
| `Conventional_UAV.avl` | Sample AVL geometry file (auto-generated on each run) |
| `sd7062.txt` | Selig SD7062 airfoil coordinates used for the main wing |
| `nTop_AVL_Integration.pdf` | Full integration guide with methodology, worked example, and parameter reference |

## License

MIT.
