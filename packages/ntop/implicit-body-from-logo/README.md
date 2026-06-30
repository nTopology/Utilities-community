# Implicit Body from Logo

Imports a .png image file and turns it into an extruded body with a given depth.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/implicit-body-from-logo/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Path` | file_path | Filepath to the .png image file. |
| `Color field` | Choice | Choose with numerical representation of the image data is used to create the body. |
| `Length` | Scalar | Image length along the y axis. |
| `Width` | Scalar | Image width along the x axis. |
| `Depth` | Scalar | Depth of the body from the image. |
| `Dot pitch` | Scalar | Sampling resolution of the image — smaller values produce higher fidelity geometry but increase computation time. |
| `Centroid` | Point | Center of the created logo |
| `X rotation angle` | Scalar | Rotation of the logo body around the X axis in degrees. |
| `Y rotation angle` | Scalar | Rotation of the logo body around the Y axis in degrees. |
| `Z rotation angle` | Scalar | Rotation of the logo body around the Z axis in degrees. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Logo` | Implicit Body | Output. |

## License

MIT.
