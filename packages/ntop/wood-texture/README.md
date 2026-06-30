# Wood Texture

Wood Texture.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/wood-texture/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Axis` | Implicit Body | The central axis to control the "Growth" |
| `Frequency` | Integer | Number of growth rings in the wood pattern. Higher values produce denser ring patterns. Try a range of 1–50 to start. |
| `Organic-ness of field` | Scalar | Generate the "organic-ness" of the field. Higher frequencies will create more chaotic patterns. Try a frequency range of 1-50 to start. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Wave` | Scalar Field | The wave generator -- based on the above inputs. |

## License

MIT.
