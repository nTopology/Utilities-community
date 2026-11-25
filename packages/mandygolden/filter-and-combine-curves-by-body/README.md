# Filter and Combine Curves by Body

Filters a list of curves using a body, then joins the curves that are kept into one polycurve.

## Install

1. Download `Filter and Combine Curves by Body.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Filter and Combine Curves by Body**.

Last saved in nTop 6.2.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Curve List | list of curve | Curves to filter and combine. |
| Body | implicit body | Implicit body used to decide which curves are kept. |

## Output

| Output | Type |
|---|---|
| Filter and Combine Curves by Body | polycurve |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
