# Union Profiles

Unions a list of profiles by extruding them, combining the bodies and extracting a section.

![Union Profiles](cover.png)

## Install

1. Download `Union Profiles.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Union Profiles**.

Last saved in nTop 5.43.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Profile List_1 | list of profile | Profiles to union. |
| Blend Type | blend type | Blend type used when combining the profiles. |
| Blend Radius | number | Blend radius used when combining the profiles. |
| Min. Feature Size | number | Smallest feature size to resolve when extracting the combined profile. |

## Output

| Output | Type |
|---|---|
| Union Profiles | profile |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
