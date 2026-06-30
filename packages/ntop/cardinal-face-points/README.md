# Cardinal Face Points

This CB will return the center point on the 'face' of the object bounding box.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/cardinal-face-points/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Input body` | Implicit Body | Implicit body to get max or min point from |
| `Index` | Integer | 0 - Bottom
1 - Top
2 - Back
3 - Front
4 - Left
5 - Right |
| `Tolerance` | Scalar | Sampling tolerance to refine the bounding box. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `OutputObject` | Point | Output. |

## License

MIT.
