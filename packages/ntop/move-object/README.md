# Move Object

This block moves the object's center to the new location provided and rotates the object if you choose.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/move-object/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Object` | Implicit Body | The implicit body to move and rotate. |
| `New Location` | Point | Target point for the object's center after the move. |
| `X Rotation Angle` | Scalar | Rotation Angle around the X axis |
| `Y Rotation Angle` | Scalar | Rotation Angle around the Y axis |
| `Z Rotation Angle` | Scalar | Rotation Angle around the Z axis |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Rotated Object` | Implicit Body | Output. |

## License

MIT.
