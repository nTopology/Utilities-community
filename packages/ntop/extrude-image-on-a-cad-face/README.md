# Extrude Image on a CAD Face

This custom block adds a bitmap image to a CAD face and extrudes it normal to the surface to the provided height.

## Recommendations

- If you are experiencing noise around your image, try enabling the `Smoothen` option. When smoothing, decrease the `Smooth Grid size` and change `Interpolation type` to cubic for best results.
- A good starting `Color field` is Grayscale. If your image has a lot of color, try a different color field — it may produce a better result.
- The `Centroid` does not need to be exactly on the face; it acts as a rough guide for positioning.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/extrude-image-on-a-cad-face/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `CAD face` | brep_face | CAD Face to add the image to |
| `Body` | Implicit Body | Body that will have the added image |
| `Bitmap` | bitmap | The imported image to extrude |
| `Centroid` | Point | The image will be centered around this location. The centroid does not need to be exactly on the face, it acts a rough guide. |
| `Length` | Scalar | The Length of the image |
| `Width` | Scalar | The Width of the image |
| `Height` | Scalar Field | Height normal to the surface |
| `Color field` | Choice | A good starting field is the grayscale, but if your image has a lot of color, you may find a different color field produces a better result. |
| `Flip Image` | bool | If you notice your words are backwards, flip the image. |
| `Rotation Angle` | Scalar | Angle to rotate the image |
| `Inverse Image` | bool | Reverse which part of the image is shown |
| `Smoothen` | bool | If you are experiencing some noise around your image, you may want to try the smoothen option. If selecting “Smoothen”, we recommend decreasing the smooth grid size and change interpolation type to cubic. |
| `Smooth Grid size` | Scalar | Input used if you choose to smoothen the image |
| `Smooth iterations` | Integer | Input used if you choose to smoothen the image |
| `Interpolation type` | interpolation_enum | Input used if you choose to smoothen the image |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Image on Face` | Implicit Body | Applying the image field to the implicit body |

## License

MIT.
