# Graph from Curve

This custom block produces a graph lattice given a curve.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/graph-from-curve/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Curve` | curve_interface | Curve to create the graph |
| `Curve refinement` | Scalar | Increment to use when sampling the curve |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Graph` | Lattice | Creates the Graph from the line segments generated from the point list |

## License

MIT.
