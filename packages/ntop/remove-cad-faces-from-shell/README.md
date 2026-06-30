# Remove CAD Faces from Shell

This custom block takes a CAD Body and multiple CAD faces and will shell the body, removing those faces from the shell.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/remove-cad-faces-from-shell/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `CAD body` | brep | The CAD body to be shelled. |
| `Faces to remove` | list<brep_face> | Where there will be an opening in the shell |
| `Tolerance` | Scalar | Used for converting the CAD body to an implicit body. |
| `Thickness` | Scalar Field | Shell Thickness |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Shelled Part` | Implicit Body | Boolean intersect the thickened remaining faces with the implicit body to remove excess. |

## License

MIT.
