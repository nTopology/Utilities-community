# Filter Point Map using CAD Faces

This Custom Block filters out a point map by excluding the result of the points near CAD faces.

- Used to filter out stress concentrations that appear on boundaries, which are typically simulation artifacts rather than real structural hotspots.
- Uses the Keep Out Distance (`KO distance`) to define a buffer zone around the CAD faces — any points within this distance are excluded from the output point map.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/filter-point-map-using-cad-faces/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Point map` | Scalar Point Map | Point Map |
| `CAD faces` | list<brep_face> | CAD Faces |
| `KO distance` | Scalar | Keep Out Distance - The distance around the CAD Faces |
| `Region` | Choice | The region you want to filter — `Outside` keeps points with distance > KO distance, `Inside` keeps points with distance < KO distance, `Boundary` keeps points with distance = KO distance |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Filtered PM` | Scalar Point Map | The new point map using the filtered points and values |

## License

MIT.
