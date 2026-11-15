# Flow solution of the closed flow body (estimate)

A GPU flow solver: incompressible lattice Boltzmann with a wall-modelled turbulence closure, half model, inlet and nozzle faired over,
conventional tail, no control deflection. Reynolds number of Mach 0.5 at 15000 ft (313 kt, dynamic pressure 209 lb/ft2); the solution itself is Mach 0. Coefficients are the surface quadrature of pressure and shear,
on wing area 143.9 ft2 and mean aerodynamic chord 6.78 ft, moments about its quarter point (station 17.53 ft).

| Angle of attack [deg] | CL | CD | Cm | Lift at this dynamic pressure [lbf] | L/D | Cells | Run time [min] |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.1181 | 0.0361 | -0.0040 | 3551 | 3.3 | 20.7 M | 42 |
| 4 | 0.3311 | 0.0544 | +0.0241 | 9957 | 6.1 | 20.8 M | 42 |

From the first and last angle: lift slope 0.0533 per deg, zero-lift angle -2.22 deg, dCm/dCL +0.132, neutral point at station 16.64 ft (12 % of the mean aerodynamic chord).
Drag from this solver on this grid is a rough number; lift and moment are the useful part.