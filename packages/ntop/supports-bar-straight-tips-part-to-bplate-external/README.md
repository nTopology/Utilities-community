# CB - Supports - Bar - Straight Tips - Part to BPlate (External)

This CB creates cylindrical bar supports with straight tips and flared base from the build plate to the part.  Supports external part surfaces only...i.e. surfaces with clear line of sight to build plate.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/supports-bar-straight-tips-part-to-bplate-external/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Part` | Implicit Body | The part to generate bar supports for. Only external surfaces with clear line of sight to the build plate will be supported. |
| `Build plane` | plane | Build Plane from which the bar supports orginate. |
| `Point Spacing` | Scalar | Spacing of points where support bars will connect to part. |
| `Overhang angle` | Scalar | Angle with respect to the build plane.  Surfaces at or below this angle necessitate support structures. |
| `Tip Offset` | Scalar | Offset between the part and the connection point |
| `Tip Thickness (Part)` | Scalar | Thickness of the tip connection at the part |
| `Tip Thickness (Bar)` | Scalar | Thickness of the tip connection to the part at the start of the support bars. |
| `Bar Thickness (Tip)` | Scalar | Thickness of the support bars at the point where the tip connection points are started. |
| `Bar Thickness (Base)` | Scalar | Thickness of the vertical support bars at the baseplate. |
| `Blend radius` | Scalar | Blend Radius of the bar supports to the build plate. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Supports Trimmed` | Implicit Body | Output. |

## License

MIT.
