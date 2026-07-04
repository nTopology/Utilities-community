# Map Coordinate Fields to Spline

Four blocks for mapping X and Y coordinate fields onto a spline. Mapping coordinate fields is part of the workflow of mapping an implicit body to a spline.

This bundle includes four blocks that employ different functions for mapping X and Y coordinate fields onto a spline: “Frenet”, “Reference Body, “Reference Direction,” and “Tangent Angle.”

Also included is a “Visualize Coordinate Mapping Functions” notebook to allow users to experiment and visualize how different functions work with different splines.

[Watch the Tutorial Video](https://youtu.be/lX0xD7rSzwg)
 

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/map-coordinate-fields-to-spline/`.

## Usage

[Watch the Tutorial Video](https://youtu.be/lX0xD7rSzwg)

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Spline` | Spline | Spline to map to |
| `Smoothen` | Bool | An option to smooth the output field to reduce artifacts |
| `X and Y Coordinate Fields` | Scalar Field List | Scalar list contains X and Y fields respectively |

## License

MIT.
