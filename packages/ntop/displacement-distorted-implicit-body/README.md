# Displacement Distorted Implicit Body

This blocks takes a Displacement Vector Point Map and turns it into a distorted body through field remapping. This block is great for visualizing what a deformed part will look like after Static Structural Analysis in nTop or from a .CSV file from external software. Because there is a decent ammount of smoothening, this block can take a bit to run.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/displacement-distorted-implicit-body/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Displacement Point Map` | vector_point_map | Displacement Vector Point Map |
| `Implicit Body` | Implicit Body | Oirignal Implicit Body |
| `Interpolation` | point_cloud_interpolation_v110_enum | Interpolation Type for Point Map to Field |
| `Grid Size` | Scalar | Grid Size used for Smoothen Field |
| `Smooth Iterations` | Integer | Amount of Smooth Iterations for Smoothen Field |
| `Smooth Interpolation` | interpolation_enum | Interpolation Type for Smoothen Field |
| `X Bounds Scale` | Scalar | Factor to scale the original Bounding Box by in X. The Bounding Box limits the amount of displacement allowed. |
| `Y Bounds Scale` | Scalar | Factor to scale the original Bounding Box by in Y. The Bounding Box limits the amount of displacement allowed. |
| `Z Bounds Scale` | Scalar | Factor to scale the original Bounding Box by in Z. The Bounding Box limits the amount of displacement allowed. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Compensated Body` | Implicit Body | Remap the original Implicit Body by using the X,Y, and Z Displacement Fields |

## License

MIT.
