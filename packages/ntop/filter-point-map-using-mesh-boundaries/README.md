# Filter Point Map using Mesh Boundaries

This Custom Block filters out a point map by excluding the result of the points in the vicinity of mesh boundaries.

- Used to filter out stress concentrations that appear on boundaries, which are typically simulation artifacts rather than real structural hotspots.
- Uses the Keep Out Distance (`KO Distance`) to define a buffer zone around the mesh boundaries — any points within this distance are excluded from the output point map.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/filter-point-map-using-mesh-boundaries/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Point Map` | Scalar Point Map | Point Map |
| `Mesh Entities` | list<mesh> | Mesh entities |
| `KO Distance` | Scalar | Keep Out Distance - The distance around the mesh elements |
| `Region` | Choice | The region you want to filter — `Outside` keeps points with distance > KO Distance, `Inside` keeps points with distance < KO Distance, `Boundary` keeps points with distance = KO Distance |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Filtered PM` | Scalar Point Map | The new point map using the filtered points and values |

## License

MIT.
