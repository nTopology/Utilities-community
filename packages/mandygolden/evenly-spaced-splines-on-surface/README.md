# Evenly Spaced Splines on Surface

Creates evenly spaced splines across an upper and a lower CAD face, guided by a reference curve, and trims them against an avoidance region.

## Install

1. Download `Evenly Spaced Splines on Surface.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Evenly Spaced Splines on Two Surfaces**.

Last saved in nTop 5.32.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Upper Face | CAD face | Upper Face for Spline |
| Lower face | CAD face | Lower Face for Spline |
| Reference Curve | curve | This ensures that both of the faces have the same starting side when generating the splines. |
| Avoidance region | implicit body | Region the splines are trimmed against. |
| Step Number | integer | Number of points to generate the spline per face |
| # of splines | integer | Number of Splines on Surface |
| Offset from Start | number | Applies an offset from the starting edge of the surface. |
| Offset from end | number | Applies an offset from the ending edge of the surface. |
| Flip UV Upper | toggle | When checked, the splines will follow the V instead of the U of the surface. |
| Flip UV Lower | toggle | Flips the UV direction of the lower face. |

## Output

| Output | Type |
|---|---|
| Evenly Spaced Splines on Two Surfaces | list of curve |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
