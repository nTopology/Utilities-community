# Mesh N-gon

Create a surface mesh with n sides. Input a large n value to approximate a circle. The block is helpful to use with the "Random Points on Mesh" block to create random points on a defined surface.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/mesh-n-gon/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Connect your input geometry / fields to the exposed inlets.
3. Tune parameters. Export via the standard nTop exporters.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Plane` | Plane | Plane on which to orient mesh |
| `Sides` | Scalar | Number of sides |
| `Radius` | Scalar | Radius of n-gon |
| `Rotate` | Scalar | Rotate the mesh around its center point |
| `Mesh n-gon` | Mesh | Main result |

## License

MIT.
