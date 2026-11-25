# Batch Part Import

Imports a Mesh List to files to a directory with a specified file name.

## Install

1. Download `Batch Part Import.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Batch Part Import**.

Last saved in nTop 5.51.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Path | text | Destination folder. Does not need a '\' at the end |
| File name | list of text | Mesh file name |
| Rotate Y to Z | toggle | When true, imported parts are rotated so the Y axis of the file becomes the Z axis. |
| Heal CAD | CAD healing option | Healing option applied to CAD files when they are imported. |
| Check Model | toggle | When true, each imported model is checked for errors on import. |

## Output

| Output | Type |
|---|---|
| Batch Part Import | list of part |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
