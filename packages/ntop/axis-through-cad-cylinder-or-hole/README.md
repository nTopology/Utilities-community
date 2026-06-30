# Axis through CAD Cylinder or Hole

This CB will create an axis through a CAD cylinder or hole. You need to define the edge you want the axis to go through and a face that is normal to that axis.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/axis-through-cad-cylinder-or-hole/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `CAD Edges` | list<brep_edge> | The CAD Edge(s) that define the hole. |
| `CAD Face` | brep_face | A CAD face the is Normal to the hole you wish to put the Axis through - typically the face adjacent to your hole. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Axis` | axis | Output. |

## License

MIT.
