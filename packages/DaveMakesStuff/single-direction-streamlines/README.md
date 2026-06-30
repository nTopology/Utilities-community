# Single Direction Streamlines

Create streamlines in one direction by trimming at seed points.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/single-direction-streamlines/`.

## Usage

1. Open the provided `.ntop` file in nTop 5.47.
2. Input vector field, domain and seed points
3. Tune parameters. Export via the standard nTop exporters.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Vector Field` | Vector Field | Vector field to apply to streamlines |
| `Domain` | Implicit Body | Domain for streamline generation |
| `Tolerance` | Scalar Value | Optional input for generating streamlines 
| `Terminal Speed` | Scalar Value | Optional input for generating streamlines |
| `Invert` | Bool | Option to return opposite section of streamlines |
| `Trimmed Streamlines` | Curves | Main result |

## License

MIT.
