# Filter Meshes by Body

Given a list of meshes, this custom block will filter any meshes that do not overlap with a body (or vice versa if you select inside body).

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/filter-meshes-by-body/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Meshes` | list<mesh> | Mesh list to filter |
| `Body` | Implicit Body | The body being used to filter the mesh list |
| `Tolerance` | Scalar | The tolerance controls the distance used to evaluate if the body and mesh intersect. A higher tolerance will result in more overlap. |
| `Inside Body` | bool | The bool that controls if you want to select meshes that lie inside the body or outside |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Filtered List` | list<mesh> | The filter block will remove any items in the list that are negative if the inside body is checked. Otherwise, it will remove any items in the list that are positive. |

## License

MIT.
