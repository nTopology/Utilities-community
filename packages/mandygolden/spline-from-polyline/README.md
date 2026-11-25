# Spline from Polyline

Fit a spline to a polyline with an approximate control of vertex rounding.

![Spline from Polyline](cover.png)

_Cover: the block run on simple example inputs (spheres, boxes, curves) set up for the picture; that example notebook is not included._

## Install

1. Download `spline from polyline.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Spline from Polyline**.

Last saved in nTop 5.37.0; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Polyline | polycurve | Polycurve to fit the spline to. |
| Approx. Round | number | Spacing used to sample points on the polyline. Larger values round the vertices more. |
| Degree | integer | Degree of the fitted spline. |

## Output

| Output | Type |
|---|---|
| Spline from Polyline | spline |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
