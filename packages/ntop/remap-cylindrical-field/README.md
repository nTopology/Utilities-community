# Remap Cylindrical Field

Remap a scalar field into a cylindrical space. The only values that will be mapped are values along the positive X-axis, and the Y-axis between -length/2 and +length/2. This block will not attempt to scale the field values to compensate for distortion. If the compensation is preferred, use the Remap Cylindrical Body block.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/remap-cylindrical-field/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Field` | Scalar Field | Scalar field to remap. |
| `Y Mapping Length` | Scalar | The length of the scalar field along the Y-axis to wrap the around the circumference of the cylindrical space. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Scalar Field_0` | Scalar Field | Output. |

## License

MIT.
