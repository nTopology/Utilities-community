# Equidistant Beams on Curve

Creates a lattice of beams starting at equally spaced points along a curve, with direction and length driven by scalar fields.

![Equidistant Beams on Curve](cover.png)

## Install

1. Download `Equidistant Beams on Curve.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Equidistant Beams on Curve**.

Last saved in nTop 5.27.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Curve | curve | Curve along which the beam start points are placed. |
| Direction | scalar field | Scalar field whose gradient sets the direction of each beam. |
| Length | scalar field | Scalar field giving the length of each beam. |
| Increment | number | Spacing between beam start points along the curve. |

## Output

| Output | Type |
|---|---|
| Equidistant Beams on Curve | graph |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
