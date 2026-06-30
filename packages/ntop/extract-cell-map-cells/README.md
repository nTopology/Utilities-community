# Extract Cell Map Cells

Extracts the Cells of a Cell Map as seperate Mesh Boxes. The boxes will be undersized from the cell by roughly 10%.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/extract-cell-map-cells/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Cell Map` | cell_map | The Cell Map to extract the cells from |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Mesh List_0` | list<mesh> | Splits the mesh faces to separate the cells |

## License

MIT.
