# Minkowski Distance

Calculate the Minkowski distance of a scalar field.

P=1 returns Manhattan distance, P=2 returns Euclidean distance, P=10+ returns Chebyshev distance. When visualizing the distance from a point, the "unit ball" is an octahedron, sphere and cube respectively. P<1 generates a concave star-like shape.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/minkowski-distance/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Input a unitless scalar field ad apply a P value.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Field` | Scalar Field | Field to modify |
| `P` | Scalar Value | Modifies the Minkowski output |
| `Minkowski Field` | Scalar Field | Output |


## License

MIT.
