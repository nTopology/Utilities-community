# Slices by Plane

This Custom Block slices an implicit body into sections of equal widths based on the choice of a slicing plane.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/slices-by-plane/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Body` | Implicit Body | Body to slice |
| `Slicing plane` | Choice | The plane to slice the body |
| `Section count` | Integer | How many sections you would like to slice the body into. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Sections` | Implicit Body List | Boolean Intersects the input body with the corresponding list of boxes. This will divide the body into the number of input sections |

## License

MIT.
