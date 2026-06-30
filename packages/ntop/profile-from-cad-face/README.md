# Profile from CAD Face

This custom block takes a flat cad face and converts it to a profile.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/profile-from-cad-face/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Flat CAD face` | brep_face | Face that will become the profile |
| `Tolerance` | Scalar | Tolerance between created profile and original CAD face. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Profile of CAD Face` | new_profile | Converts the CAD Face to an implicit and extracts the profile of the face from the location of the plane. |

## License

MIT.
