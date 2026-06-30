# True False Field

This custom block creates a field composed of 0s and 1s. If the translation location = 0, the field will equal 1 at all positive values of the field and 0 for negative values of the field. To reverse this, check the Flip input. This can be useful when adding ramps or only applying a ramp to a certain section by multiplying this field with another.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/true-false-field/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Scalar field` | Scalar Field | The field you want to modify |
| `Flip` | bool | Changes the positive or negative assignment |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Ramp` | Scalar Field | Assigns binary values to the input scalar field |

## License

MIT.
