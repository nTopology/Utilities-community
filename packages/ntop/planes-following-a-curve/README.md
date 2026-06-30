# Planes Following a Curve

This custom block outputs planes spaced at the given distance a part and have a z direction normal to the surface and a x direction that follows the provided curve.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/planes-following-a-curve/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Curve` | curve_interface | Curve for planes to follow |
| `Body` | Implicit Body | Implicit that the plane will be normal to |
| `Line Spacing` | Scalar | How close the intervals are for determining the tangent vector along the curve. The smaller the line spacing, the clower the vector will be to following the curve. |
| `Dist between Planes` | Scalar | Spacing between consecutive output planes along the curve. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Destination Plane` | list<plane> | Output. |

## License

MIT.
