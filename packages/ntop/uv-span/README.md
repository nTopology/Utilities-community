# UV Span

This custom block will calculate the span in the U or V direction of a CAD Face.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/uv-span/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Face` | brep_face | The CAD Face to analyze |
| `U or V Span` | Choice | The direction you want to obtain the span of |
| `Divisions` | Scalar | The number of divisions will determine how many cells are created in the U or V direction. If you have a part with a lot of curvature, we recommend a higher number of divisions. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Output` |  | Output. |

## License

MIT.
