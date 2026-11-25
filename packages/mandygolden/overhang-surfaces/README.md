# Overhang Surfaces

This custom block locates regions that require support based on a given overhang angle and direction.

## Install

1. Download `Overhang Surfaces.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Overhang Surfaces**.

Last saved in nTop 5.44.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Mesh | mesh | Mesh to check for overhang regions |
| Implicit | implicit body | Implicit body used to measure the overhang angle. |
| Overhang angle | number | Overhang angle beyond which a surface is treated as needing support. |
| Direction | vector | Direction for locating areas of overhang |

## Output

| Output | Type |
|---|---|
| Overhang Surfaces | mesh |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
