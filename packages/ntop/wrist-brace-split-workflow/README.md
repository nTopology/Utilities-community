# Advanced Wrist Brace Workflow

This notebook walks through how to create a wrist brace with a voronoi and other lattices throughout the design. This is the advanced version of two nTop Files for the Wrist Brace Application Workbook, and this notebook also covers how to split the wrist brace into two parts and add connector geometry. For the file without these advanced steps, please review the  "Wrist Brace Workflow".

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/advanced-wrist-brace-workflow/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Thickness of Arm Brace` | Scalar | Wall thickness of the brace shell. |
| `Beam Thickness` | Scalar Field | Thickness of the lattice beams inside the brace. |
| `Clearance` | Scalar | Gap between mating parts to account for fit and assembly tolerance. |
| `Point count` | Integer | Number of voronoi cells created. |
| `Rim Thickness` | Scalar | Thickness of the solid rim border running around the edge of the brace. |
| `# of Connectors` | Integer | Number of Connectors on the cut line per side |
| `Connector Dist from Edge` | Scalar | How close the connectors will be placed to the edge of the wrist brace |
| `Split Plane` | plane | This plane and angle will determine how the brace is split into two sections. Change the angle to change the location of the split. |
| `Gap Thickness` | Scalar | Defining how large the gap is when splitting the two sections into two. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |

## License

MIT.
