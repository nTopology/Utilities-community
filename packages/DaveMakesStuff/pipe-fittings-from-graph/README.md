# Pipe Fittings from Graph

Add aesthetic "pipe fittings" to a graph. To remove bolts set "Bolt Diameter" to 0. Adjusting "Edge Correction" corrects inaccuracies in the orientation of bolts that sometimes occurs at shape edges. This is a novelty application for education and learning purposes.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/DaveMakesStuff/pipe-fittings-from-graph/`.

## Usage

1. Open the provided `.ntop` file in nTop 4.12+.
2. Select graph to modify
3. Define parameters to modify graph

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Graph` | Graph | Graph to modify |
| `Tube Diameter` | Scalar Value | Diameter of main tubes |
| `Sleeve Length` | Scalar Value | Length of sleeve extending from vertex |
| `Sleeve Diameter` | Scalar Value | Diameter of sleeve |
| `Bolt From Center` | Scalar Value | Distance of bolts from vertex |
| `Bolt Diameter` | Scalar Value | Diameter of bolts. Input "0" for no bolts |
| `Edge Correction` | Scalar Value | Corrects inaccuracies in the orientation of bolts that sometimes occurs at shape edges. |

## License

MIT.
