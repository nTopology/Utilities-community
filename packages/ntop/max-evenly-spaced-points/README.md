# Max Evenly Spaced Points

This custom block creates almost evenly spaced points on a body based on a desired point spacing using a hexagonal packaging approach.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/max-evenly-spaced-points/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Mesh` | Mesh | A Mesh of the part (or Mesh of a Surface)  you want to put points on. |
| `Point spacing (mm)` | Scalar | Desired spacing between points. |
| `Body` | Implicit Body | The Implict Body you want to put points on. |
| `Relaxation iterations` | Integer | Number of iterations to evenly distribute the points on the mesh. |
| `Random seed` | Integer | Seed value to generate randomness. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Closest Points` | list<closest_point_properties> | Output. |

## License

MIT.
