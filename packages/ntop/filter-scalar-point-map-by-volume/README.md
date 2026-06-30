# Filter Scalar Point Map by Volume

Filters a scalar point map by volume. There are options for inside, outside and on the boundary for filtering the points.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/filter-scalar-point-map-by-volume/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Scalar Point Map` | Scalar Point Map | The point map to be filtered. |
| `Volume` | Implicit Body | The implicit body defining the volume region used to filter points. |
| `Region` | Choice | Options: Inside / Outside / Boundary |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Filtered point map` | Scalar Point Map | Final filtered point map |

## License

MIT.
