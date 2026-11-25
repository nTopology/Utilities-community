# Filter Zero Bodies

Removes bodies from a list when their bounding box is not larger than the tolerance in X, Y or Z.

## Install

1. Download `Filter Zero Bodies.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Remove Zero Bodies**.

Last saved in nTop 5.43.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Implicit Body List | list of implicit body | List of implicit bodies to filter. |
| Tolerance | number | Bodies whose bounding box span is not larger than this in any direction are removed. |

## Output

| Output | Type |
|---|---|
| Remove Zero Bodies | list of implicit body |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
