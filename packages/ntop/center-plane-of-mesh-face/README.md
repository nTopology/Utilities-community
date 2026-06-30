# Center Plane of Mesh Face

Given a face, this custom block will place four random points on the face and then create a plane that is normal to the first three points and is centered between all four points. For best results choos either a small portion of a mesh face or a flat face.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/center-plane-of-mesh-face/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Mesh Face` | Mesh | The mesh face to sample points from and derive the center plane. For best results use a small or flat face. |
| `Flip Normal` | bool | Reverses the plane normal direction. Use if the output plane is pointing away from the intended side. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Center Plane` | plane | Output. |

## License

MIT.
