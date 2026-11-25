# 2D Point Grid

This custom block produces a 2D or 3D grid of points based on the given number of points along the x,y and z axis and the distance between those points.

![2D Point Grid](cover.png)

_Cover: the block run on simple example inputs (spheres, boxes, curves) set up for the picture; that example notebook is not included._

## Install

1. Download `2D Point Grid.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **2D Point Grid**.

Last saved in nTop 4.15.3; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Starting Location | point | Corner point where the grid starts. |
| X # of Points | integer | Number of points along the X axis. |
| X Point Distance | number | Distance between points along the x axis. Even if there is only on point, you must input a value. |
| Y # of Points | integer | Number of points along the Y axis. |
| Y Point Distance | number | Distance between points along the y axis. Even if there is only on point, you must input a value. |
| Flip X Direction | toggle | When true, the grid extends in the negative X direction from the starting location. |
| Flip Y Direction | toggle | When true, the grid extends in the negative Y direction from the starting location. |

## Output

| Output | Type |
|---|---|
| 2D Point Grid | list of point |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
