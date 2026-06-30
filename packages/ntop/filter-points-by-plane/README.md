# Filter Points by Plane

Filters a scalar point map to retain those within the negative  field of a plane.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/filter-points-by-plane/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Point map` | Scalar Point Map | The point map that will be filtered. |
| `Cut plane` | plane | Plane used to divide the point map. Points on the negative side of the plane are retained in the output. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Filtered Points` | Scalar Point Map | Output. |

## License

MIT.
