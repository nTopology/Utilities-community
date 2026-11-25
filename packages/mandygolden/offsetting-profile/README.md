# Offsetting Profile

Offsets a profile by a given distance and returns the offset profile.

## Install

1. Download `Offsetting Profile - mod.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Offsetting Profile**.

Last saved in nTop 5.33.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Profile | profile | Profile to offset. |
| Build Plane | plane | Plane that the profile lies in. |
| Profile offset | number | Distance the profile is offset by. |
| Perimeter | polycurve | Polycurve outlining the profile, used to drive the offset. |

## Output

| Output | Type |
|---|---|
| Offsetting Profile | profile |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
