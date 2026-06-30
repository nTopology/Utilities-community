# Extrude CAD Face

This custom block extrudes a CAD face normal to the surface up to a given height.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/extrude-cad-face/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Face` | brep_face | Face to extrude |
| `Height` | Scalar Field | Height of extrusion |
| `Flip direction` | bool | Check to reverse the direction of the extrusion |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Extrusion` | lattice_body | Creates a lattice using a solid box as the unit cell. This creates a solid extrusion from the CAD Face |

## License

MIT.
