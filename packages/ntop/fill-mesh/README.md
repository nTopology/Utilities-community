# Fill Mesh

This custom block will take in an open mesh and will create a solid that is within the same bounds.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/fill-mesh/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Open Mesh` | Mesh | The open mesh that needs to be filled |
| `Flip Direction` | bool | If your faces are not facing towards each other, we recommend you flip the direction to get the desired results. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final` | Implicit Body | Performs a boolean intersect on the Implicit Face scalar field, and the mesh bounding box solid box, to create a solid region where the two overlap. |

## License

MIT.
