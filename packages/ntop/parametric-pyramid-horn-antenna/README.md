# Parametric Pyramid Horn Antenna

This block synthesizes a Pyramid Horn Antenna by iterating to find an optimal χ (Chi) value. It generates a 3D manifold including the feed waveguide and flared aperture. Refer to the Technical Diagram for dimension mapping: A/B (Aperture) and L1/L2 (Slant Lengths).

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/parametric-pyramid-horn-antenna/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Desired Gain (dBi)` | Scalar | Desired Gain (dBi) |
| `f [Hz]` | Scalar | Design Frequency [Hz] |
| `a [cm]` | Scalar | Waveguide Broad Wall (a) |
| `b [cm]` | Scalar | Waveguide Narrow Wall (b) |
| `Waveguide - L [cm]` | Scalar | Waveguide Length [cm] |
| `t [cm]` | Scalar | Thickness [cm] |
| `+/- % Variation of χi for Sampling` | Scalar | Optimization Search Window (%) For example, if the Initial Chi value is 100 and the % Variation defined is 15, the Sampling Range will be define between  85 - 115. |
| `Number of Design Points` | Integer | This value defines the number of sample points or design points you which to run. It takes the Sample Range, previously defined, and simply divides by this value. |
| `% Tolerance to Check` | Scalar | Convergence Tolerance (%) |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Pyramid Horn: Waveguide + Aperature` | Implicit Body | Generates the final 3D manifold by boolean-subtracting the inner hollow volume from the external horn-waveguide shell based on the calculated slant lengths P_E and P_H. |

## License

MIT.
