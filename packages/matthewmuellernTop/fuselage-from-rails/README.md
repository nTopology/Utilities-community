# Fuselage from Rails

Create a fuselage from rails using Conic Section Sweeps. Top and Bottom tangent is set to +Y, Side tangent is set to +/- Z. All rails should have a starting point in the X=0 plane. Top and Bottom rails should be planar in XZ with the nose pointed in the -X direction. Side rail can be non-planar, but should be kept in +Y. If end points of rails do not line up in X, the minimum X value will be used to close the fuselage.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities-community.git
```

The package lives at `packages/matthewmuellernTop/fuselage-from-rails/`.

## Usage

1. Open the provided `.ntop` file in nTop 6.0+.
2. Connect your input geometry / fields to the exposed inlets.
3. Tune parameters. Export via the standard nTop exporters.

## Inputs & outputs

| Name | Type | Notes |
|------|------|-------|
| `Top` | Curve | Top rail. Should start at X=0, be planar in XZ, with the nose pointed in the -X direction. |
| `Side` | Curve | Side rail. Can be non-planar, but should be kept in +Y with a starting point at X=0. |
| `Bottom` | Curve | Bottom rail. Should start at X=0, be planar in XZ, with the nose pointed in the -X direction. |
| `Top Rho` | Real Field | Rho value controlling the conic section sweep tangency for the Top rail. |
| `Bottom Rho` | Real Field | Rho value controlling the conic section sweep tangency for the Bottom rail. |
| `Tip Close Blend Radius` | Real | Blend radius used when closing the fuselage at the nose (tip). |
| `Rear Close Blend Radius` | Real | Blend radius used when closing the fuselage at the tail (rear). |
| `Closed Fuselage` (output) | Implicit Body | The resulting closed fuselage body. |

## License

MIT.
