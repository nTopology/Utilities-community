# Text Label on Part

This custom block applies a text label engraving or embossing on a part.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/text-label-on-part/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Body` | Implicit Body | Body that will have the label |
| `Location` | Point | Approximate location for the text. This will later be placed directly on the surface, so no need for this to be exact. |
| `Text` | Text | Text to be converted to an implicit |
| `Letter spacing` | Scalar | Spacing between each letter (this is applied before the transformation) |
| `Length` | Scalar | Length of the entire text string (before warping it to the surface) |
| `Width` | Scalar | Width of the entire text string (before warping it to the surface) |
| `Rotate` | Scalar | Rotate around the normal to the surface |
| `Thickness` | Scalar | Thickness of engraving/embossing. |
| `Lock ratio` | bool | If you want to lock the ratio between the length and the width, check this option and then use the scale choice to only use the length or width when defining the size. |
| `Scale` | Choice | If you want to lock the ratio between the length and the width, check the lock ratio and then use the scale choice to only use the length or width when defining the size. |
| `Displayed on body` | Choice | Choose to either apply an emboss or an engraving |
| `Text region` | Implicit Body | The text will be confined to this defined region. If you want this on a specific mesh or CAD face, try using the one sided offset or extrude CAD face and choose that as the text region |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Body` | Implicit Body | Choose to engrave or emboss |

## License

MIT.
