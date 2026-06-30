# Voronoi Surface Lattice with KOZ

This custom block creates a Voronoi Surface Lattice that avoids input Keep Out Zones (KOZ)

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/voronoi-surface-lattice-with-koz/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Body` | Implicit Body | The body that will have the surface voronoi |
| `Keep out zones` | Implicit Body List | Areas to avoid. Spheres work best, but you can also use other geometry as well. |
| `Mesh tolerance` | Scalar | Used to create the surface lattice |
| `Additional gap` | Scalar Field | If the lattice still is intersecting the part, increase this additional gap input. |
| `Point count` | Integer | Number of points used for the voronoi surface region. |
| `Spatial weighting` | Scalar Field | An optional input to cntrol the spacing of the generated points. |
| `Beam thickness` | Scalar Field | The beam thickness of the resulting lattice |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Voronoi` | voronoi_surface_lattice_body | Generates the Voronoi Lattice |

## License

MIT.
