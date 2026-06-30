# Perforate with Normal Holes

Creates a random distribution of normal-direction holes in one or more surfaces.  It lets the user specify an exact quantity of holes that are randomly distributed and somewhat equally spaced.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/perforate-with-normal-holes/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Outer Hole Diameter` | Scalar | Hole diameter on the outer surface(s) of the part. |
| `Inner Hole Diameter` | Scalar | Hole diameter on the inner surface(s) of the part. |
| `Max Part Thickness` | Scalar | Part thickness, which will be the same as the depth of the holes. |
| `Point Count` | Integer | Total quantity of holes on the surface(s). |
| `Relaxation Iterations` | Integer | Equalizes point spacing. Larger value will take longer to process but will result in more equally spaced holes. |
| `Thin Wall Body` | Implicit Body | Implicit body on which holes are desired. |
| `CAD Face(s)` | list<brep_face> | CAD face(s) on which holes will be placed. If using more than 1 CAD face, all faces must be adjacent. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `FINAL Body` | Implicit Body | Output. |

## License

MIT.
