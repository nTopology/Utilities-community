# Cross Sectional Area Max-Min

This block returns the largest and smallest cross-sectional area of an implicit body, as well as their Z locations, as a two-item list. Index 0 is the max area slice; index 1 is the min area slice.

To inspect the area value of a slice, drag and drop the cross-sectional area chip from that slice in the nTop graph.

## When to use this

In additive manufacturing, cross-sectional area directly affects print time, material consumption, and thermal behavior at each layer. Use this block to:

- **Predict thermal hot spots** — sudden jumps between max and min area indicate stress concentrations and residual heat buildup during printing
- **Validate build orientation** — compare max cross-sectional area across different orientations to find the orientation with the lowest peak area

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/cross-sectional-area-max-min/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Implicit Body` | Implicit Body | The implicit body to evaluate |
| `Slice Layer Height` | Scalar | The layer height at which the body is sliced to compute cross sections |
| `Feature Size` | Scalar | The feature size of the slices |
| `Include Negative Z` | Bool | Enable if the body extends into negative Z space to ensure the entire body is sliced |
| `Frame` | Frame | Frame to redefine the coordinate system if needed |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Combined Lists` | List\<Slice\> | Two-item list of slices — index 0 is the max area slice, index 1 is the min area slice. Drag and drop the cross-sectional area chip from each slice to read its area value |

## License

MIT.
