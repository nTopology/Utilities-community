# Trim Curve at Point

Trim a curve at a point with option to select which side to keep.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/trim-curve-at-point/`.

## Usage

1. Open the provided `.ntop` file in nTop 5.47.
2. Input curve and point

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Curve` | Curve | The curve to trim |
| `Point` | Point | The point at which to trim the curve |
| `Invert` | Bool | An option to return curve section on other side of point |
| `Output` | Curve | Trimmed curve |

## License

MIT.
