# Cell Size from Number of Cells

Calculates the cell size that fits approximately the requested number of cells into the bounding box of a model.

## Install

1. Download `Cell Size from Number of Cells.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Cell Size from Number of Cells**.

Last saved in nTop 5.34.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Virtual Model | model | Model whose bounding box sets the volume to fill with cells. |
| Number of Cells | number | Approximate number of cells to fit in the bounding box. |

## Output

| Output | Type |
|---|---|
| Cell Size from Number of Cells | number |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
