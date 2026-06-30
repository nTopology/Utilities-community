# Select CAD Faces by Containment

This custom block selects CAD faces that are contained inside a region. The entire bounding box of each face must be contained.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/select-cad-faces-by-containment/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `CAD Body` | brep | CAD Body to extract faces from |
| `Region` | Implicit Body | Region used to select faces |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Any_0` | list<brep_face> | Evaluates each face based on the Region field. If the faces max and min points are both within the region, the face is selected. |

## License

MIT.
