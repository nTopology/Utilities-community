# Text along a Curve on Body

This custom block takes a line of text and converts it to an implicit body. This uses the Arial Bold Font.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/text-along-a-curve-on-body/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Text` | Text | Text to be converted to an implicit |
| `Curve` | curve_interface | Curve that the text will follow. Recommendation: Place the curve on the body for the best results. |
| `Body` | Implicit Body | The text will be placed on the body aligned by the normal of the body surface and the provided curve. |
| `Letter spacing` | Scalar | Approximate spacing between each letter. |
| `Height` | Scalar | Height of one Letter |
| `Width` | Scalar | Width of one Letter |
| `Depth` | Scalar | Text depth |
| `Displayed on body` | Choice | Choose to apply either an emboss or engraving. |
| `Blend radius` | Scalar Field | Blend radius between the text and the body |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Body` | Implicit Body | Output. |

## License

MIT.
