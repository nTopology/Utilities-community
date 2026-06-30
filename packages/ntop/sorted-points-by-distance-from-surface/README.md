# Sorted Points by Distance from Surface

This custom block sorts a set of points based on the distance from a surface of a given implicit.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/sorted-points-by-distance-from-surface/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Point list` | Point List | Points for sorting |
| `Body` | Implicit Body | Body to compare for distance when sorting |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Sorted` | Point List | Sorts the point list based on the line lengths |

## License

MIT.
