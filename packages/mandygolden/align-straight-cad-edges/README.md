# Align Straight CAD Edges

This custom block will align two cad bodies based on an edge from each and face next to that edge at the centroid of that edge. To change rotation of the part, change the angle.

## Install

1. Download `Align Straight CAD Edges.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Align Straight CAD Edges**.

Last saved in nTop 3.27.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| CAD body 1 | CAD body | Independent -- will not move positions |
| Edge 1 | CAD edge | Must be a straight edge to work properly |
| Face 1 | CAD face | Face of CAD body 1 that borders Edge 1. Its orientation sets the alignment plane. |
| CAD body 2 | CAD body | Will snap to location |
| Edge 2 | CAD edge | Must be a straight edge to work properly |
| Face 2 | CAD face | Face of CAD body 2 that borders Edge 2. Its orientation sets the alignment plane. |
| Angle | number | Additional rotation applied after the edges are aligned. |

## Output

| Output | Type |
|---|---|
| Align Straight CAD Edges | CAD body |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
