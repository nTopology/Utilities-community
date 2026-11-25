# Mass Flow Rate

Translates a mass flow rate to a velocity boundary conditioin

## Install

1. Download `Mass Flow Rate.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Mass Flow Rate**.

Last saved in nTop 5.23.0; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Boundary | boundary | Boundary to apply boundary condition |
| Mass Flow Rate | number | Mass Flow Rate |
| Direction | vector | Flow direction |
| Area | number | Cross sectional area |
| Density | number | Material density |

## Output

| Output | Type |
|---|---|
| Mass Flow Rate | velocity |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
