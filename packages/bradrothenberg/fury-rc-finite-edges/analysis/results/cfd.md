# Flow solution of the closed flow body (estimate)

A GPU flow solver: incompressible lattice Boltzmann with a wall-modelled turbulence closure, half model, inlet and nozzle faired over,
conventional tail, no control deflection. Reynolds number of Mach 0.5 at 15000 ft (313 kt, dynamic pressure 209 lb/ft2); the solution itself is Mach 0. Coefficients are the surface quadrature of pressure and shear,
on wing area 143.9 ft2 and mean aerodynamic chord 6.78 ft, moments about its quarter point (station 17.53 ft).

| Angle of attack [deg] | CL | CD | Cm | Lift at this dynamic pressure [lbf] | L/D | Cells | Run time [min] |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | -0.0190 | 0.0099 | +0.0434 | -572 | -1.9 | 20.5 M | 25 |
| 4 | 0.2236 | 0.0197 | +0.0508 | 6725 | 11.4 | 20.2 M | 24 |
| 8 | 0.4770 | 0.0540 | +0.0398 | 14343 | 8.8 | 19.9 M | 23 |
| 12 | 0.7166 | 0.1135 | +0.0236 | 21549 | 6.3 | 19.8 M | 26 |

From the first and last angle: lift slope 0.0613 per deg, zero-lift angle +0.31 deg, dCm/dCL -0.027, neutral point at station 17.72 ft (28 % of the mean aerodynamic chord).
Drag from this solver on this grid is a rough number; lift and moment are the useful part.