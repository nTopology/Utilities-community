# Plane from CAD Face

This block locates a plane on a given CAD Face. It needs supplied a CAD Face which denotes the origin point of the plane, and two CAD Edges, which define the axis of the plane.

## Install

1. Download `Plane from CAD Face.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Plane from CAD Face**.

Last saved in nTop 3.37.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| CAD Face | CAD face | Select the CAD face on which you want the plane located. The blocks pulls the centroid data from the CAD Face's bounding box, so it works best with planar faces |
| CAD Edge 1 | CAD edge | This CAD Edge is used to define the X-Axis of the plane |
| CAD Edge 2 | CAD edge | This CAD Edge is used to define the Y-Axis of the Plane |
| Flip Normal | toggle | Use this check box to invert the normal direction of the created plane |

## Output

| Output | Type |
|---|---|
| Plane from CAD Face | plane |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
