# Implicit Axis

This custom block takes in an implicit and will output the axis for the part in either the U, V or W direction.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/implicit-axis/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Implicit` | Implicit Body | The implicit body to reference for creating the axis. |
| `Along axis` | Choice | The Axis direction |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Axis` | axis | Creating the Axis using the line segment length and direction |

## License

MIT.
