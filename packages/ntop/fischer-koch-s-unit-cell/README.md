# Fischer Koch S Unit Cell

Creates a custom unit cell from a Fischer-Koch S surface periodic pattern field with options for wall thickness and midsurface offset.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/fischer-koch-s-unit-cell/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Unit Cell Type` | Choice | Type of parametrized unit cell — `0`: Walled (solid walls), `1`: Offset (offset surface only), `2`: Walled + Offset (combination of both) |
| `Cell Size` | Scalar | Size of one unit cell in mm. Controls the overall scale of the periodic pattern. |
| `Approx. Wall Thickness` | Scalar | Approximate thickness of the TPMS walls in mm. |
| `Midsurface Offset` | Scalar | Offset of the TPMS as a positive or negative approximate distance. Positive values shift the mid-surface wall outward; negative values shift it inward. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Custom Unit Cell` | Unit Cell | Fischer-Koch S unit cell ready for use in lattice workflows. |

## License

MIT.
