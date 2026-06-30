# **Parametric Impeller**

This parametric notebook generates high-fidelity pump geometry by combining a drafted central column with exponentially twisted primary and secondary vanes, all driven by adjustable fluid dynamics parameters like twist rate, vane count, and radial taper.

## **What you get**

* **Complex Vane Morphologies:** Primary and secondary vanes with independent height and count controls.  
* **Advanced Twist Control:** Exponentially ramped twist rates to optimize flow behavior at the vane tips.  
* **Manufacturing Ready:** Integrated radial draft angles and central column blending for castability or 3D printing.  
* **Robust Field Logic:** Implicit modeling ensures clean Booleans and predictable offsets for downstream shelling or simulation.

## **Inputs**

| Name | Type | Notes |
| ----- | ----- | ----- |
| `Vanes Max Height` | Scalar | Maximum height of the primary vanes. |
| `Vanes Primary Count` | Integer | Total number of primary vanes in the polar array. |
| `Secondary Vanes Height` | Scalar | Height multiplier for the secondary vanes. |
| `Min Radius` | Scalar | The inner radius at the top of the vanes. |
| `Max Radius` | Scalar | The overall outer radius of the impeller. |
| `Top Vane Taper` | Angle | Taper angle of the vane cutouts at the top. |
| `Linear Twist Rate` | Twist Rate | Base twist rate applied to the vanes (deg/mm). |
| `Top Twist Ramp` | Twist Rate | Exponential increase of twist near the vane tips. |
| `Exp. k Factor` | Scalar | Growth factor for the exponential twist ramp. |
| `Plate Thickness` | Scalar | Thickness of the bottom mounting plate. |
| `Column Radius` | Scalar | Radius of the central mounting column. |
| `Center Blend Radius` | Scalar | Radius of the blend between the plate and column. |
| `Vane Thickness` | Scalar | Nominal wall thickness of the vanes. |
| `Draft Angle` | Angle | Radial draft applied to vanes for mold release. |
| `Hole Radius` | Scalar | Radius of the central shaft hole. |

## **Outputs**

| Name | Type | Notes |
| ----- | ----- | ----- |
| `Final Solid` | Implicit Body | The completed impeller geometry, ready for simulation or export. |

## **Modeling Principles**

* **Late Trimming:** To maintain field integrity, all components are modeled as "infinite" bodies and intersected with a master domain at the final step.  
* **Normalized Fields:** The twist operation uses normalized distance fields to prevent thickness distortion during high-twist maneuvers.  
* **Interactive Polar Arrays:** Utilizes a custom remap-based polar array for faster performance and better field continuity than standard geometry-based arrays.

## **License**

MIT.