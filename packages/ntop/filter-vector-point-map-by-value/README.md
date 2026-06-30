# Filter Vector Point Map by Value

This Custom Block filters out a Vector Point Map based on a condition and a reference value.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/filter-vector-point-map-by-value/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Vector point map` | vector_point_map | Vector Point Map |
| `Condition` | comparison_enum | Condition |
| `Component` | Choice | Vector component |
| `Value` | Scalar | Filtering Value |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Filtered Point Map` | vector_point_map | The Filtered Point Map |

## License

MIT.
