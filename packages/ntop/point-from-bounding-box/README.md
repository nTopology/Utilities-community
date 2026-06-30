# Point from Bounding Box

Input an implicit body and extract a point on the bounding box based on the min, max, or centroid values of the bounding box in x, y, and z.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/point-from-bounding-box/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Body` | Implicit Body | Body to extract the point from |
| `X` | Choice | Location of the point in the x direction. |
| `Y` | Choice | Location of the point in the y direction. |
| `Z` | Choice | Location of the point in the z direction. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Point` | Point | Output. |

## License

MIT.
