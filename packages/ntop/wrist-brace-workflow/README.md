# Wrist Brace Workflow

This notebook walks through how to create a wrist brace with a voronoi and other lattices throughout the design. This is the simplified version of two nTop Files for the Wrist Brace Application Workbook. To learn how to split the wrist brace into two parts and add connector geometry, please review the "Advanced Wrist Brace Workflow".

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/wrist-brace-workflow/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Wrist Brace Thickness` | Scalar | Wall thickness of the brace shell. |
| `Beam Thickness` | Scalar Field | Thickness of the lattice beams inside the brace. |
| `Clearance` | Scalar | Gap between mating parts to account for fit and assembly tolerance. |
| `Point Count` | Integer | Number of voronoi cells created. |
| `Rim Thickness` | Scalar | Thickness of the solid rim border running around the edge of the brace. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |

## License

MIT.
