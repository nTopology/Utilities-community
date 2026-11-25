# Plane Aligned with Two Fields

This custom block will produce a plane that is normal to a given field and aligned to an additional field.

## Install

1. Download `Plane Aligned with Two Fields.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Plane Aligned with Two Fields**.

Last saved in nTop 4.11.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Origin | list of point | Origin of the planes. |
| Normal field | scalar field | The plane will be normal to this field (surface, implicit, etc.) |
| Perpendicular field | scalar field | The Y axis will be aligned to this field. |

## Output

| Output | Type |
|---|---|
| Plane Aligned with Two Fields | list of plane |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
