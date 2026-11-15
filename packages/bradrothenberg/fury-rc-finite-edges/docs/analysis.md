# Analysis results

All numbers are estimates made on the model, in US customary units. Scripts are in `analysis/`; the json beside each result keeps SI values.

## Weights, fuel and centre of gravity (estimate)

Bodies of the model with assumed densities. The structure is a representative layout, not a stressed design: read these as
first estimates. Stations are measured aft of the nose tip.

- Length 33.5 ft, span 24.85 ft, wetted area 797 ft2, enclosed volume 311 ft3
- Reference wing (input trapezoid to the centreline): area 143.9 ft2, aspect ratio 4.29, taper 0.165, mean aerodynamic chord 6.78 ft with its leading edge at station 15.84 ft

| Body | Volume [ft3] | Weight [lb] | Station of centroid [ft] | Height [in] | Basis |
|---|---:|---:|---:|---:|---|
| Skin | 7.97 | 796 | 19.92 | 6.5 | wetted area x skin thickness |
| Fuselage frames | 1.23 | 213 | 18.19 | 6.4 | 173 lb/ft3 |
| Wing spars | 0.25 | 44 | 18.41 | 2.2 | 173 lb/ft3 |
| Wing ribs | 0.14 | 25 | 19.00 | 2.2 | 173 lb/ft3 |
| Tail structure | 0.10 | 17 | 30.51 | 22.2 | 173 lb/ft3 |
| Engine | 13.38 | 650 | 27.26 | 13.7 | published dry weight, placed at the centroid of the envelope |
| Jet pipe | 0.15 | 42 | 32.10 | 13.7 | 277 lb/ft3 |
| Forward fuselage fuel | 36.31 | 1604 | 13.67 | 9.0 | usable fuel = cell volume x usable fraction |
| Centre fuselage fuel | 36.50 | 1612 | 17.78 | 8.1 | usable fuel = cell volume x usable fraction |
| Aft fuselage fuel | 25.10 | 1108 | 23.05 | 9.6 | usable fuel = cell volume x usable fraction |
| Wing fuel | 13.62 | 601 | 18.28 | 3.0 | usable fuel = cell volume x usable fraction |
| Mission systems bay | 19.40 | 0 | 6.39 | 8.8 | space, no weight assigned |
| Inlet duct air | 40.63 | 0 | 17.62 | 2.4 | space, no weight assigned |

| Total | Weight [lb] | Centre of gravity station [ft] | % of mean aerodynamic chord |
|---|---:|---:|---:|
| Structure (skin, frames, spars, ribs) | 1095 | 19.66 | 56 |
| Engine and jet pipe | 692 | 27.55 | 173 |
| Usable fuel (734 US gal) | 4926 | 17.69 | 27 |
| Modelled items, no fuel | 1786 | 22.72 | 101 |
| Modelled items, full fuel | 6712 | 19.03 | 47 |

Fuel cells hold 834 US gal geometric volume; 88 % is counted usable: 4926 lb of JP-8.
This is the packing limit of the model: every fuselage bay between the tank bulkheads is filled, and so is the wing box. A real aircraft gives part of that
space to landing gear, weapons and systems, so its fuel load is lower.
Landing gear, systems, mission equipment and stores are not modelled, so the centre of gravity above is of the modelled items only.
With the reported 4000 lbf engine, thrust / weight of the modelled items at full fuel is 0.60.
The 5,000 lb maximum take-off weight often quoted for the Fury goes with the 20 ft by 17 ft size quoted for the earlier design; it is not used here
because the photographs give a 33.5 ft aircraft (docs/proportions.md).

Assumptions: skin_density = 1600.0, structure_density = 2770.0, jet_pipe_density = 4430.0, fuel_density = 804.0, usable_fuel_fraction = 0.88, engine_weight_lb = 650.0, engine_thrust_lbf = 4000.0.

## Inlet duct (estimate)

Cuts of the duct air body of the model. Areas are normal to the duct centreline. Mach numbers are one-dimensional, isentropic, for an assumed
Mach number at the engine face; no losses, boundary layer or distortion.

| Quantity | Value |
|---|---:|
| Lower lip station | 9.78 ft |
| Throat station | 10.28 ft |
| Engine face station | 24.96 ft |
| Capture area (largest section at the lip, seen from the front) | 330 in2 |
| Throat area | 330 in2 (43.1 in wide, 12.0 in high) |
| Engine face area | 418 in2 (23.1 in diameter) |
| Capture area / throat area | 1.00 |
| Engine face area / throat area | 1.27 |
| Length, throat to engine face | 14.67 ft = 7.6 face diameters |
| Centreline rise, throat to engine face | 21.9 in = 0.12 of the length |
| Steepest centreline slope | 14 deg |
| Engine face seen straight through the inlet | 0 % |

| Condition | Engine face Mach (assumed) | Air flow [lb/s] | Throat Mach | Stream tube / capture area |
|---|---:|---:|---:|---:|
| Sea level, static | 0.35 | 81 | 0.47 | static |
| Sea level, static | 0.45 | 99 | 0.64 | static |
| Sea level, static | 0.55 | 114 | choked | static |
| Sea level, Mach 0.3 | 0.35 | 85 | 0.47 | 1.45 |
| Sea level, Mach 0.3 | 0.45 | 104 | 0.64 | 1.78 |
| Sea level, Mach 0.3 | 0.55 | 121 | choked | 2.05 |
| 35,000 ft, Mach 0.85 | 0.35 | 33 | 0.47 | 0.73 |
| 35,000 ft, Mach 0.85 | 0.45 | 40 | 0.64 | 0.89 |
| 35,000 ft, Mach 0.85 | 0.55 | 46 | choked | 1.03 |

![duct](img/duct.png)

## Lift and stability by vortex lattice (estimate)

Flat lifting surfaces from the planform inputs. No fuselage volume, thickness or camber: the fuselage moves the real neutral point forward
and reduces the real directional stability, so read the numbers as a comparison of the two tails and a first estimate.

Reference: wing area 143.9 ft2, span 24.85 ft, mean aerodynamic chord 6.78 ft, its leading edge at station 15.84 ft.

| Tail | Area [ft2] | Arm [ft] | Volume coefficient |
|---|---:|---:|---:|
| Horizontal tail (both sides) | 48.8 | 12.3 | 0.61 |
| Fin | 17.3 | 12.5 | 0.060 |
| V-tail (both panels, cant 47 deg) | 49.0 | 12.6 | horizontal 0.29, vertical 0.092 |

| Mach | Configuration | Lift slope [per deg] | Neutral point station [ft] | Neutral point [% MAC] | Cn beta of the lifting surfaces [per rad] | CY beta [per rad] |
|---:|---|---:|---:|---:|---:|---:|
| 0.0 | Wing alone | 0.0662 | 17.77 | 28 | -0.000 | -0.001 |
| 0.0 | Conventional tail | 0.0747 | 19.02 | 47 | -0.120 | -0.236 |
| 0.0 | V-tail | 0.0730 | 18.84 | 44 | -0.176 | -0.340 |
| 0.6 | Wing alone | 0.0930 | 17.80 | 29 | -0.000 | -0.002 |
| 0.6 | Conventional tail | 0.1032 | 18.91 | 45 | -0.157 | -0.311 |
| 0.6 | V-tail | 0.1018 | 18.82 | 44 | -0.231 | -0.447 |

Centre of gravity of the modelled items (structure, engine, fuel; no landing gear, systems or stores) from analysis/results/mass.md:
full fuel at station 19.03 ft, no fuel at station 22.72 ft.
- Conventional tail: lattice neutral point is -0 % MAC aft of the full-fuel point and -55 % MAC aft of the no-fuel point (positive = stable, before the fuselage effect).
- V-tail: lattice neutral point is -3 % MAC aft of the full-fuel point and -57 % MAC aft of the no-fuel point (positive = stable, before the fuselage effect).

## Flow solution of the closed flow body (estimate)

A GPU flow solver: incompressible lattice Boltzmann with a wall-modelled turbulence closure, half model, inlet and nozzle faired over,
conventional tail, no control deflection. Reynolds number of Mach 0.5 at 15000 ft (313 kt, dynamic pressure 209 lb/ft2); the solution itself is Mach 0. Coefficients are the surface quadrature of pressure and shear,
on wing area 143.9 ft2 and mean aerodynamic chord 6.78 ft, moments about its quarter point (station 17.53 ft).

| Angle of attack [deg] | CL | CD | Cm | Lift at this dynamic pressure [lbf] | L/D | Cells | Run time [min] |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.1181 | 0.0361 | -0.0040 | 3551 | 3.3 | 20.7 M | 42 |
| 4 | 0.3311 | 0.0544 | +0.0241 | 9957 | 6.1 | 20.8 M | 42 |

From the first and last angle: lift slope 0.0533 per deg, zero-lift angle -2.22 deg, dCm/dCL +0.132, neutral point at station 16.64 ft (12 % of the mean aerodynamic chord).
Drag from this solver on this grid is a rough number; lift and moment are the useful part.

Geometry revision: the flow body of these runs was made before the diverter slot and the splitter plate were added to the model. The inlet is faired over in the flow body, so the change is local to the inlet; the runs were not repeated on the final shape.

## The two aerodynamic estimates side by side

the vortex lattice (wing and tail only, no fuselage) gives a lift slope of 0.0747 per deg and a neutral point at station 19.02 ft; the flow solution of the whole aircraft gives 0.0533 per deg and station 16.64 ft, 2.4 ft (35 % of the mean aerodynamic chord) further forward. A long, wide forebody with chines does move the neutral point forward, but the flow solution is two angles on one grid with no grid study, so neither number is settled. The full-fuel centre of gravity of the modelled items (station 19.03 ft) is at the lattice neutral point and 35 % of the chord behind the flow-solution one: as modelled, with every bay full and no landing gear, systems or payload, the aircraft is not shown to be statically stable. Treat the centre of gravity and stability as open.

## Notebook against the Python model

The outer mold line was meshed in nTop at a tolerance of 0.47 in and the Python field evaluated at every mesh vertex. Conventional tail (the final shape with diverter and splitter plate): 5.1 M triangles, 99 % of the vertices within 1.9 thousandths of an inch of the Python field, largest difference 0.09 in. V-tail (before the diverter and splitter plate were added): 5.0 M triangles, 99 % of the vertices within 1.9 thousandths of an inch of the Python field, largest difference 0.09 in. Panel grooves and paint films are not part of the outer mold line and were not meshed in nTop.
