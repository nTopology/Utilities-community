# Conformal Spiral to Body

This custom block creates a spiral that is conformal to an implicit body.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/conformal-spiral-to-body/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Implicit Body` | Implicit Body | Body that the spiral will conform to |
| `Starting Point` | Point | Starting point of the spiral (recommended: bottom center point of the implicit body) |
| `Spiral Direction` | Vector | The normal direction the spiral will rotate around |
| `Number of Rotations` | Scalar | The number of rotations in the spiral |
| `Tolerance` | Scalar | Used in operations to create the conformal curve. Decrease if the curve is not conformal; increase if the block is slow to compute |
| `Increment Size` | Scalar | Controls the number of points used to generate the spiral. A smaller value produces a better-conforming spline |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Spiral` | spline | Orients the Spline to ensure it wraps around the implicit body |

## License

MIT.
