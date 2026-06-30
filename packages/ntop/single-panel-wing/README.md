# Single Panel Wing

Create a Single Panel Wing driven by Root Chord Length, Wing Span, QC Angle, and Taper Ratio.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/single-panel-wing/`.

## Usage

1. Open the provided `.ntop` file in nTop 5.45+.
2. Add the Single Panel Wing custom block in your notebook.
3. Define the Root Point to position the wing relative to your fuselage.
4. Adjust the Quarter Chord Angle and Dihedral Angle to set the wing's orientation and stability characteristics.
5. Control the wing's shape using Root Chord Length, Wing Span, and Taper Ratio.
6. Apply aerodynamic washout by adjusting the Twist Mag.
7. The output is a mirrored Implicit Body, providing a full wing assembly symmetrical across the global plane.

## Inputs & outputs

| Name | Type | Description |
| ----- | ----- | ----- |
| `Root Point` | Point | The frontmost point where the wing attaches to the fuselage. |
| `Root Chord Length` | Scalar | Wing length from front to back at the root. |
| `Wing Span` | Scalar | Full span of both wings (tip-to-tip). |
| `Quarter Chord Angle` | Scalar | Sweep angle measured at 25% chord line; positive values sweep back, negative sweep forward. |
| `Taper Ratio` | Scalar | Ratio of tip chord to root chord (defines how much the wing narrows). |
| `Twist Mag` | Scalar | The magnitude of angular twist (washout) from root to tip. |
| `Dihedral Angle` | Scalar | The upward V-angle of the wings for lateral stability. |
| **Output** | **Implicit Body** | The final generated, twisted, and mirrored wing geometry. |

## License

MIT.
