# Text to Implicit

This custom block takes a line of text and converts it to an implicit body. This uses the Arial Bold Font.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/text-to-implicit/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Text` | Text | Text to be converted to an implicit |
| `Letter spacing` | Scalar | Spacing between each letter (this is applied before the transformation) |
| `Location` | Point | The center of the text string will be placed at this location. |
| `X rotation angle` | Scalar | Use if you would like to rotate the object around the x axis |
| `Y rotation angle` | Scalar | Use if you would like to rotate the object around the y axis |
| `Z rotation angle` | Scalar | Use if you would like to rotate the object around the z axis |
| `Length` | Scalar | Length of the entire text string |
| `Width` | Scalar | Width of the entire text string |
| `Depth` | Scalar | Text depth |
| `Lock ratio` | bool | If you want to lock the ratio between the length and the width, check this option and then use the scale choice to only use the length or width when defining the size. |
| `Scale` | Choice | If you want to lock the ratio between the length and the width, check the lock ratio option and then use the scale choice to only use the length or width when defining the size. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Word` | Implicit Body | Output. |

## License

MIT.
