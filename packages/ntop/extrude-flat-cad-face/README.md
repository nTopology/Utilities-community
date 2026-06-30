# Extrude Flat CAD Face

This custom block takes a flat cad face and will extrude it normal to the face.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/extrude-flat-cad-face/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Flat CAD Face` | brep_face | The CAD Face you want to extrude |
| `Extrusion Distance` | Scalar | The distance to extrude the face |
| `Flip Direction` | bool | Option to flip the extrusion direction normal |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Extrusion` | Implicit Body | Extrudes the profile based on the input extrusion distance |

## License

MIT.
