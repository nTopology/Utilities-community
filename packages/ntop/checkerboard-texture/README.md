# Checkerboard Texture

Returns an infinite checkerboard field along one axis with values of 0 and 1.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/checkerboard-texture/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Cell Size` | Scalar Field | Size of a single period of the checkerboard (always define units) |
| `Location` | Point | Location of the starting point of a unit |
| `Direction` | Vector | Normal direction of the patterned field |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Oriented Checkerboard` | Scalar Field | Orient to desired location and axis |

## License

MIT.
