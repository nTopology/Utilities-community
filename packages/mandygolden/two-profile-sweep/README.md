# Two Profile Sweep

This custom block generates a sweep with one profile on one side and transitions to a different profile on the other end of the curve.

## Install

1. Download `Two Profile Sweep.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Two Profile Sweep**.

Last saved in nTop 5.48.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Profile | profile | Profile at the start of the sweep. |
| Profile2 | profile | Profile at the end of the sweep. |
| Curve | spline | Curve the profiles are swept along. |
| Continuity | continuity option | Continuity of the transition between the two profiles. |

## Output

| Output | Type |
|---|---|
| Two Profile Sweep | scalar field |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
