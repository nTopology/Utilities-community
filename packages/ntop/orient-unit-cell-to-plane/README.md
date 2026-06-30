# Orient Unit Cell to Plane

Places the input unit cell at the list of input points. It gives the user the ablity to adjust the rotation of the unit cell along it's axis, rotate the unit cell about a vector and translate the unit cell along it's axis. In addition it requires a 'Rotation Axis' as an input which will allow the user to rotate the unit on surfaces/plane parallel to the build plane. It will also automatically compute and place points on the desired input surface via the CAD Face Mesh and Object to Perforace inputs. The final addition, allows to user to input selected CAD edges and define a keep out zone from while no points will be generated.

## Installation

Clone this repo or copy the package folder into your nTop workspace:

```bash
git clone https://github.com/nTopology/Utilities.git
```

The package lives at `packages/ntop/orient-unit-cell-to-plane/`.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `Unit Cell (UC)` | Mesh | Make sure align in z originally. Also use the center of the unit cell to place points, this can be changed in the source plane block in the orient plane block |
| `UC Spacing (mm)` | Scalar | Desired spacing between perforation pattern. |
| `Radii: UC Xsec (mm)` | Scalar | This value can be between the minimum radii or maximum radii of an inscribed or circumscribed circle on a Cross Section of your Unit Cell.

For example, if we have a square cross section:

Min Value = the distance between the center point and a bisected edge of a the square.

Max Value =  the distance between the center point and a corner of a the square. |
| `Object to Perforate` | Implicit Body | The implicit body you want to perforate. |
| `CAD Face Mesh` | Mesh | A mesh of the CAD faces you want to perforate. |
| `Relaxation iterations` | Integer | Number of iterations to evenly distribute the points on the mesh. |
| `Random seed` | Integer | Seed value to generate randomness. |
| `Angle to twist` | Scalar | Rotates the Unit Cell about its axis. |
| `'draft' Vector` | Vector | Define the vector you wish to rotate/tilt in. For example, if tilting in the z direction enter 0,0,1 etc |
| `Angle to 'draft'` | Scalar | Rotates the Unit Cell about it's centroid based off the 'draft' Vector |
| `Nom. Thickness (mm)` | Scalar | The nominal thickness of the part you are perforating. 

This will help ensure the Unit Cell penetrates the part by translating it along its axis. |
| `Rotation Axis` | Scalar Field | This will generally be the primary axis of object you want to perforate. |
| `CAD Edge KOZ` | list<brep_edge> | A set of CAD Edges you wish to use as, Unit Cell Keep Out Zone (KOZ). This will be used to remove points near the Edges. Select edges on the surface you are selecting above. |
| `Radius of KOZ` | Scalar Field | Define the size of the Keep Out Zone (KOZ). This value will define an exclusion zone around the CAD Edge. |

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `Merge Mesh Output` | Mesh | Positions a single unit cell at each of the point locations. The angle and positioning inputs are applied at this step. The output is a single mesh of all the positioned unit cells. |

## License

MIT.
