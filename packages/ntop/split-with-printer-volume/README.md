# Split with Printer Volume

This custom block will split a body into different sections to fit inside the printer using the rectangular cell map.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/split-with-printer-volume/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Body` | Implicit Body | Body to Split |
| `Start location` | Point | To change where the split is located, you can move the start location |
| `Printer volume` | bounding_box | Bounding box representing the usable build volume of the printer. The body will be split into sections that fit within this volume. |
| `Perimeter gap` | Scalar | Space between the edge of the printer volume and the body. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Split` | Implicit Body List | Removes any implicit body with no resulting body |

## License

MIT.
