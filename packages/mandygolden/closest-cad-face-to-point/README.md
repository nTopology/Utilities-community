# Closest CAD Face to Point

This block finds the closest CAD face in a CAD body to a given point. Useful in circumstances where the face IDs in a CAD part may change (and colored faces aren't available). Works with point lists, too.

## Install

1. Download `Closest CAD Face to Point.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Closest CAD Face to Point**.

Last saved in nTop 4.3.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| CAD body | CAD body | CAD body whose faces are searched. |
| Search point | point | Point to search from |

## Output

| Output | Type |
|---|---|
| Closest CAD Face to Point | CAD face |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
