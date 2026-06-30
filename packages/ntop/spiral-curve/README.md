# Spiral Curve

This custom block creates a spiral curve based on the given inputs.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/spiral-curve/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Starting Point` | Point | Starting location of the spiral |
| `Direction` | Vector | Direction of the spiral created |
| `Height` | Scalar | Height of the spiral |
| `Radius` | Scalar | Radius that the spiral follows |
| `Number of Rotations` | Scalar | Total number of full 360° turns in the spiral. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Spiral` | curve_interface | Spiral through the points. |

## License

MIT.
