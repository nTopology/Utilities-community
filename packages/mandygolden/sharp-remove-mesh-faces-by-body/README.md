# Sharp Remove Mesh Faces by Body

Removes the part of a mesh that lies inside a body and returns a mesh with sharp edges, by converting through an implicit body.

## Install

1. Download `Sharp Remove Mesh Faces by Body.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Sharp Remove Mesh Faces by Body**.

Last saved in nTop 4.25.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Mesh | mesh | Mesh to remove faces from. |
| Body | implicit body | Body whose volume is removed from the mesh. |
| Tolerance | number | Tolerance used when converting the result back to a mesh. |
| Origin | point | Origin for the initial face selection |

## Output

| Output | Type |
|---|---|
| Sharp Remove Mesh Faces by Body | mesh |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
