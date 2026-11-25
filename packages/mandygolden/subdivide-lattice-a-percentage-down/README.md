# Subdivide Lattice a Percentage Down

This block adds a vertex in the center of each beam of lattice. Nest this block in additional instances of the same block to subdivide further.

## Install

1. Download `Subdivide Lattice a Percentage Down.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Subdivide Lattice a Percentage Down**.

Last saved in nTop 6.1.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Lattice | lattice body | Lattice body to subdivide. |
| Thickness | scalar field | Beam thickness of the resulting lattice. |
| Subdivision location | number | Fraction along each beam where the new vertex is placed. |

## Output

| Output | Type |
|---|---|
| Subdivide Lattice a Percentage Down | lattice body |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
