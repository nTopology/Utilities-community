# Catenary Spline From Line

Create a "sagging" spline from a line using "Length Factor" input to modify amount of sag.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/catenary-spline-from-line/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Input line and Length Factor
3. Adjust "Count" value to minimize computation time

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Line` | Line| Line to create catenary spline from |
| `Length` | Scalar Value | Controls amount of sag |
| `Count` | Integer Value | Number of points used to plot spline. Larger values will improve resolution but require more computation time. |
| `Output Spline` | Spline | Main result |

## License

MIT.
