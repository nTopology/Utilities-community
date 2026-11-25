# Adjust Starting Point of Curve

Change the starting point of a curve to match a given element number.

## Install

1. Download `Adjust Starting Point of Curve.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Adjust Starting Point of Curve**.

Last saved in nTop 6.3.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Curve | polycurve | Polycurve whose segments are reordered so a different segment becomes the start. |
| Element Number | integer | Number of the segment that becomes the first segment of the new polycurve. |
| flip order | toggle | When true, the new polycurve is reversed so it runs in the opposite direction. |

## Output

| Output | Type |
|---|---|
| Adjust Starting Point of Curve | polycurve |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
