# Trimmed Curve from Track

Trims a polycurve at a location found with a midsurface curve and extends the trimmed end.

## Install

1. Download `Trimmed Curve from Track.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Trimmed Curve for Track**.

Last saved in nTop 6.2.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Polycurve to trim | polycurve | Polycurve that is trimmed. |
| Midsurface Curve | curve | Curve used to locate where the polycurve is cut. |
| Cut Distance | number | Distance from the located position at which the curve is cut. |
| Extension distance | number | Length the trimmed curve is extended by. |
| flip order | toggle | When true, the order of the polycurve segments is reversed. |

## Output

| Output | Type |
|---|---|
| Trimmed Curve for Track | polycurve |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
