# Four Fischer Koch TPMS Custom Unit Cells

Generate a Custom Unit Cell from Fischer Koch C, CY, S or Y TPMS fields with options to bias the field or select wall output. 

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/four-fischer-koch-tpms-custom-unit-cells/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Select which TPMS field to use when generating custom block
3. input desired offset or wall thickness values

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Fischer Koch` | Choice | Select from Fischer Koch C, CY, S or Y TPMS fields |
| `Offset` | Scalar value | Amount to offset the field |
| `Wall` | Bool | Check to generate a walled surface |
| `Wall Thickness` | Scalar value | Thickness of wall |
| `Custom Unit Cell` | Custom Unit Cell | Main output |

## License

MIT.
