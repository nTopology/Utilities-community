# Export Temperature Point Map

This custom block exports a temperature point map as a CSV Table

## Install

1. Download `Export Temperature Point Map.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Export Temperature Point Map**.

Last saved in nTop 5.18.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Temperature Point Map | temperature point map | Point map whose point coordinates and temperatures are exported to the table. |
| Precision | integer | The number of significant figures for formatting the output as text |
| Path | file path | When you name the file, make sure you include .csv |

## Output

| Output | Type |
|---|---|
| Export Temperature Point Map | table_file_data |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
