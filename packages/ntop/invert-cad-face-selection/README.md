# Invert CAD Face Selection

Removes specified CAD Faces from a list of CAD Faces

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/invert-cad-face-selection/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Remove Faces` | list<brep_face> | Faces to remove |
| `All faces` | list<brep_face> | All of the faces in the CAD body |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Inverted selection` | list<brep_face> | Filters All CAD Faces to remove any faces that meet the condition |

## License

MIT.
