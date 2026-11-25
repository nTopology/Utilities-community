# Midcurve Between Two Curves

Creates a curve midway between two curves by sampling points on each curve, joining matching points with lines and fitting a curve through the midpoints.

## Install

1. Download `Midcurve Between Two Curves.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Midcurve Between Two Curves**.

Last saved in nTop 6.3.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Curve 1 | curve | First curve. |
| Curve 2 | curve | Second curve. |
| Curve Increment | number | Spacing between the sample points on the curves. |

## Output

| Output | Type |
|---|---|
| Midcurve Between Two Curves | curve |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
