# Rotate Vector Field with Axis Field

Rotate  local vectors in a vector field around local vectors in an "axis" vector field. Define the amount of rotate with an scalar field in degrees.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities-community.git
```

The package lives at `packages/DaveMakesStuff/rotate-vector-field-with-axis-field/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Input appropriate vector and scalar fields

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Field to Rotate` | Vector Field | The field to rotate |
| `Axis Field` | Vector Field | The vectors in this field will serve as local axis around which to rotate that the above field  |
| `Angle` | Scalar Field | Defines the amount of local rotation |
| `Rotated Field` | Vector Field | Output field |

## License

MIT.
