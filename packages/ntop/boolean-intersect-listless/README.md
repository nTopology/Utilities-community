# Boolean Intersect [Listless]

Create an Implicit Body where the input bodies spatially overlap.  Functions in the same way as a Boolean Intersect block, but does not uses lists and only accepts 2 inputs.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/boolean-intersect-listless/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Object A` | Implicit Body | First implicit body to intersect. |
| `Object B` | Implicit Body | Second implicit body to intersect. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Intersected Geometry` | Implicit Body | Performs the Boolean Intersect between the two bodies |

## License

MIT.
