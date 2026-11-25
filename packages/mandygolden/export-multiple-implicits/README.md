# Export Multiple Implicits

This block will export one or more mesh files. If the input mesh is list of n meshes, then n mesh files will be saved.

## Install

1. Download `Export Multiple Implicits.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Export Multiple Implicit Bodies**.

Last saved in nTop 5.10.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Implicit Body List | list of implicit body | List of implicit bodies to export, one file per body. |
| Path | file path | File path used to name the exported files. |

## Output

| Output | Type |
|---|---|
| Export Multiple Implicit Bodies | list of implicit_body_file |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
