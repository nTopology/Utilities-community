# STDEV

In statistics, the standard deviation is a measure of the amount of variation or dispersion of a set of values. A low standard deviation indicates that the values tend to be close to the mean of the set, while a high standard deviation indicates that the values are spread out over a wider range.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/stdev/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Scalar List` | Scalar List | Samples to compute data metric |
| `Trimming Threshold` | Scalar | Trimming Threshold from 0-0.5.  A value of 0.1 removes 10% of the largest and smallest values of the dataset. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Standard Deviation` | Scalar | Output. |

## License

MIT.
