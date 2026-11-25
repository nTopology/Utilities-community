# Ramped Points on Curve

Creates points along a curve with a spacing that ramps between Out Min and Out Max as the position along the curve moves from In Min to In Max.

## Install

1. Download `Ramped Points on Curve.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Ramped Points on Curve**.

Last saved in nTop 5.32.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Curve_1 | curve | Curve to place points on. |
| In Min | scalar field | Position along the curve where the ramp starts. |
| In Max | scalar field | Position along the curve where the ramp ends. |
| Out Min | number | Spacing at the start of the ramp. |
| Out Max | number | Spacing at the end of the ramp. |
| Curve Tolerance | number | Tolerance used when approximating the curve. |

## Output

| Output | Type |
|---|---|
| Ramped Points on Curve | list of point |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
