# Side Duct Body

Creates an air duct implicit body that transitions from a parallelogram cross-section at the inlet to a circular cross-section at the outlet. The duct follows a user-defined spline path from inlet to outlet.

## Inputs

| Name | Type | Description |
|------|------|-------------|
| Inlet Location | Point | 3D position of the duct inlet center |
| Inlet Width | Real (length) | Width of the parallelogram cross-section at the inlet |
| Inlet Height | Real (length) | Height of the parallelogram cross-section at the inlet |
| Inlet Radius | Real (length) | Blend radius smoothing the inlet cross-section corners |
| Inlet Angle | Real (angle) | Side angle of the parallelogram at the inlet |
| Outlet Location | Point | 3D position of the duct outlet center |
| Outlet Radius | Real (length) | Radius of the circular cross-section at the outlet |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| Bounded | Implicit | The bounded duct implicit body |

## Notes

- The duct path is defined by a spline connecting the inlet and outlet locations. Path curvature is controlled by **Path Start Tension** and **Path End Tension** internal parameters (default 1.27).
- **Transition Continuity** controls the smoothness of the cross-section transition along the path (default: tangent continuous).
- The outlet diameter is computed as `2 × Outlet Radius`.
- A **Butt Line Zero** reference plane is established at the origin for coordinate alignment.
