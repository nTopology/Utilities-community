# Order Points Using Hilbert Curve

Orders a list of points on the XY plane according to position along a Hilbert Curve.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities-community.git
```

The package lives at `packages/DaveMakesStuff/order-points-using-hilbert-curve/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Input points to be ordered
3. Select number of Hilbert Curve iterations
4. Use the "Polycurve" block to visualize how output points are ordered and adjust iterations as needed.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Points` | Point List | Points to be ordered |
| `Iterations` | Choice | Select number of iterations to perform on Hilbert Curve from 1 to 8. |
| `Ordered Points` | Point List | Output point list |

## License

MIT.
