# Spiral Field

This custom block takes a radius and creates an involute that begins with that radius created. Equations used: https://math.stackexchange.com/questions/411855/implicit-representation-of-the-involute-of-a-circle/415023

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/spiral-field/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Radius` | Scalar | Spiral Radius |
| `Center` | Point | Spiral Center |
| `Normal` | Vector | The spiral will curve around this normal |
| `Spiral Direction` | Choice | The rotation direction you would like the spiral to turn |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Output` |  | Output. |

## License

MIT.
