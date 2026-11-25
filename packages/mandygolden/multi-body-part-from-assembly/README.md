# Multi-Body Part from Assembly

This block will turn a part that has a list of CAD components in nTop into a part that is one list of CAD bodies instead. A separate file with the same name will be added to the same directory but with a .x_t extension

## Install

1. Download `Multi-Body Part from Assembly.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Multi-Body Part from Assembly**.

Last saved in nTop 4.25.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Part file path | file path | System path of part file |
| Rotate Y to Z | toggle | For a part coming from CAD systems like SolidWorks and Creo that use a Y-up coordinate system, rotate it so Z becomes the up direction. |
| Heal CAD | CAD healing option | Set level of automatic healting for CAD on import. This healing does not apply to x_t and x_b files. |
| Check Model | toggle | Check the imported model for defects such as self-intersecting or degenerate features. Turning this option off will import models faster, but not detect defects that could lead to downstream modeling issues. It is generally recommended to leave this option on. |

## Output

| Output | Type |
|---|---|
| Multi-Body Part from Assembly | part |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
