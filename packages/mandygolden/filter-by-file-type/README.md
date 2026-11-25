# Filter by File Type

This custom will filter by file type.

## Install

1. Download `Filter by File Type.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Filter by File Type**.

Last saved in nTop 5.51.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| File Names | list of text | List of file names to filter. |
| File Types | list of text | File types to match against the file names. |
| Keep | toggle | If checked, it will keep this data type in the list. If unchecked, it will remove the files of that type. |

## Output

| Output | Type |
|---|---|
| Filter by File Type | list of text |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
