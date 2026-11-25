# Top Opt Supports

This CB attempts to use the topology optimizer to create support structures and/or self supporting geometry for a given part. This CB is mainly meant to package this method into a sharable form. Users are highly encouraged to bring parts "under the hood" to fully learn the process and manipulate the workflow further for their needs.

## Install

1. Download `Top Opt Supports.ntop`.
2. In nTop, import it from the Custom Blocks panel (or open the file to see how the block is built).
   The block appears as **Top Opt Supports**.

Last saved in nTop 5.44.2; checked to open in nTop 6.4.3.

## Usage

Add the block to a notebook, wire the inputs below, and use its output downstream.

## Inputs

| Input | Type | Description |
|---|---|---|
| Part | implicit body | Part that needs supports. |
| Build Plane | plane | Build plane currently needs to be oriented such that +z aligns with global coordinate system. |
| Overhang angle | number | Overhang angle beyond which a surface is treated as needing support. |
| Supports from Build Plate Only | toggle | Select this to have build supports originate from only the build plate.  Leaving this unchecked allows build supports to originate from upskin part surfaces as needed. |
| Top Opt Iterations | integer | Number of topology optimization iterations. |
| Stay-Away Distance | number | Distance supports stay away from part. |
| Offset Distance | number | Offset distance from part for the outer boundary of the "design space" used by the top opt. |
| Top Opt Passive Region Tolerance | number | The passive region is where material must be left by the top opt operation. A positive value will effectively extend this region.  This is sometimes necessary to help areas that are disconnected or unsupported connect in certain scenarios. |
| Mesh Top Opt Restraint Area | toggle | If areas of unexpected support material occur, selecting this may help eliminate such areas. |
| Passive Region Percentage Filter | number | Adjust this percentage to remove small unwanted passive regions.  Only active when Mesh Top Opt Restraint Area is toggled on. Value is the mesh face count size of the largest passive region as a percentage. |
| Feature Size | number | The minimum feature size used to discretize the manufacturing support volume body.  This input will affect the resolution of the support volume and the speed of the algorithm.  Sharp edges that need support may require a smaller value. |
| Smoothen Grid Size | number | Size of the sampled grid spacing when smoothening the top opt result. |
| Smooth Iterations | integer | Number of smoothing iterations applied to the result. |
| Smooth Interpolation Type | interpolation type | Interpolation type used when smoothing the result. |
| Threshold | number | Top opt result threshold to use for smoothening |
| Iteration | integer | Top opt result iteration to use for smoothening |

## Output

| Output | Type |
|---|---|
| Top Opt Supports | implicit body |

## License

MIT License, copyright nTop; see `LICENSE`. Block descriptions were tidied with AI assistance (Claude).
