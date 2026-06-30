# Field from Fluid Domain - 6.1

This Custom Block will allow users the generate an Implicit Body from a Point Map, by letting users define Lower and Upper Bounds they wish to truncate (i.e. eliminate) in order to shape the new geometry. Version 6.1 has fewer inputs exposed over 6.0

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/field-from-fluid-domain-6-1/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `CSV Point Map` | Scalar Point Map | Input a Unit Less Point Map. |
| `Field Definition Steps` | Text | Section label grouping the field definition workflow steps. |
| `Lower Bound` | Scalar | The lower bound defines the minium value you wish to keep, values below will be truncated. This input is unit less. |
| `Upper Bound` | Scalar | The upper bound defines the maximum value you wish to keep, values above will be truncated. This input is unit less. |
| `Field to Implicit Steps` | Text | Section label grouping the field-to-implicit conversion steps. |
| `Field Resolution` | Scalar | The granularity of this value will impact resolution of the field but also increase computation time. A good starting value should be 0.01mm. If the Implicit body generated is outside the bounds of the point map, decrease this value.

This value needs to be less than 1.0 and greater than 0.0 |
| `Grid Size` | Scalar | This value will need to be iterated upon until the final implicit lies within the truncate set of Points. It's easiest to turn the point visiblity on while going through this process.

A good starting value at the moment seems to be ~3-4x + the Build/Tolerance Size |
| `Mesh Steps` | Text | Section label grouping the meshing workflow steps. |
| `Mesh Tolerance` | Scalar | Size of the sampled grid spacing. An example starting point would be 30% of the mesh size used to run your CFD.

In most cases a final Smoothen Body operation will be required at the very end |
| `Min. feature size` | Scalar | Option to specify the approximate size of the smallest feature(s) of the implicit body that should be preserved during the conversion. when provided, features that are smaller than this input will be filtered out and not included in the final result. This is not a Minimuim Element Size control. |
| `Final Smoothen` | Text | Section label grouping the final smoothing steps. |
| `Smooth Iterations` | Integer | This value will need to be iterated upon until the final implicit lies within the truncate set of Points. It's easiest to turn the point visiblity on while going through this process. You should not need to exceed 3. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Final Body` | Implicit Body | Step 8: Final Smoothen of CSV to Implicit |

## License

MIT.
