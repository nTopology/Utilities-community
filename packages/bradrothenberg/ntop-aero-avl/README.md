# nTop AeroDeck Generator

A production-ready Python pipeline that ingests nTop panel geometry exports and automatically generates comprehensive aerodynamic decks using AVL and XFOIL, with both human-readable reports and machine-readable output files for downstream 6-DOF simulation.

> **Source repository:**
> **[https://github.com/bradrothenberg/nTopAero_AVL](https://github.com/bradrothenberg/nTopAero_AVL)**

## Features

- **Automated Pipeline** — Load nTop CSV exports → Generate AVL input → Run analysis → Create aero deck
- **Comprehensive Validation** — Geometry validation with detailed error/warning reporting
- **AVL + XFOIL Integration** — Automated execution with batch processing and cached airfoil polars
- **PDF Reports** — Auto-generated reports covering static/dynamic stability, control effectiveness, and dynamic modes
- **6-DOF Ready Output** — Machine-readable JSON aerodeck for downstream simulation
- **Flexible Configuration** — YAML-based configuration for all analysis parameters

## Requirements

- Python 3.9+
- [AVL](https://web.mit.edu/drela/Public/web/avl/) (Mark Drela, MIT)
- [XFOIL](https://web.mit.edu/drela/Public/web/xfoil/) (optional, for airfoil polars)

## Installation

```bash
git clone https://github.com/bradrothenberg/nTopAero_AVL
cd ntop-aerodeck
pip install -e .
```

## nTop Export Requirements

Export your aircraft geometry from nTop as the following CSV files:

| File | Description |
|------|-------------|
| `mass.csv` | Mass, CG, and inertia tensor |
| `LEpts.csv` | Leading edge panel points (x, y, z) |
| `TEpts.csv` | Trailing edge panel points (x, y, z) |
| `WINGLETpts.csv` | *(Optional)* Winglet geometry points |
| `ELEVONpts.csv` | *(Optional)* Control surface hinge line points |

## Quick Start

```bash
# Full pipeline — AVL + XFOIL + spanwise loads for FEA
aerodeck build /path/to/ntop_export/ --verbose

# Custom load factor (default: 6g)
aerodeck build /path/to/ntop_export/ -g 4.0 --verbose

# AVL only (no XFOIL)
aerodeck generate /path/to/ntop_export/ -v

# Validate geometry without running analysis
aerodeck validate /path/to/ntop_export/
```

## Output Files

| File | Description |
|------|-------------|
| `{name}.avl` | AVL geometry input (human-readable) |
| `{name}.mass` | AVL mass file |
| `{name}_aerodeck.json` | Full aero deck for 6-DOF simulation |
| `{name}_aerodeck.pdf` | Comprehensive analysis report |
| `avl_outputs/` | Raw AVL text outputs |
| `polars/*.csv` | Cached XFOIL airfoil polars |

## PDF Report Contents

- Summary: metadata, reference geometry, mass properties
- Static stability derivatives (CL_α, Cm_α, Cn_β, neutral point)
- Dynamic stability derivatives (CL_q, Cm_q, Cl_p, Cn_r, …)
- Roll-yaw coupling characteristics
- Dynamic modes (Dutch roll, spiral, roll subsidence)
- Control effectiveness and trim requirements
- Elevon forces and hinge loading

## License

MIT — see the [source repository](https://github.com/bradrothenberg/nTopAero_AVL) for details.

## Authors

Brad Rothenberg

## Acknowledgments

AVL and XFOIL by Mark Drela (MIT).
