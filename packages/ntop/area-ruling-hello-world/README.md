# Area Ruling Hello World

Area ruling demo. Goal: Optimize the 8 parameters so the red curve (actual area ruling) matches the target curve (green curve). Difference is quantified with the RMSE between the values. Other quantifications could be used instead if they work better.

[Sears-Haack Body](https://en.wikipedia.org/wiki/Sears%E2%80%93Haack_body)

*Antonsen, June 2025*

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/area-ruling-hello-world/`.

## Inputs

All parameters are dimensionless geometric scalars in the range 0–1.

| Name | Type | Description |
| --- | --- | --- |
| `Height Param 1` | Scalar | Controls the height of the area ruling profile at the first control point. Range: 0–1. |
| `Height Param 2` | Scalar | Controls the height of the area ruling profile at the second control point. Range: 0–1. |
| `Height Param 3` | Scalar | Controls the height of the area ruling profile at the third control point. Range: 0–1. |
| `Height Param 4` | Scalar | Controls the height of the area ruling profile at the fourth control point. Range: 0–1. |
| `Width Param 1` | Scalar | Controls the width of the area ruling profile at the first control point. Range: 0–1. |
| `Width Param 2` | Scalar | Controls the width of the area ruling profile at the second control point. Range: 0–1. |
| `Width Param 3` | Scalar | Controls the width of the area ruling profile at the third control point. Range: 0–1. |
| `Width Param 4` | Scalar | Controls the width of the area ruling profile at the fourth control point. Range: 0–1. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `RMSE` | Scalar | Root Mean Square Error between the actual area ruling curve and the target Sears-Haack curve. Lower values indicate a closer match. |

## License

MIT.
