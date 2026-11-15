# Weights, fuel and centre of gravity (estimate)

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
because the photographs give a 33.5 ft aircraft (reference/PROPORTIONS.md).

Assumptions: skin_density = 1600.0, structure_density = 2770.0, jet_pipe_density = 4430.0, fuel_density = 804.0, usable_fuel_fraction = 0.88, engine_weight_lb = 650.0, engine_thrust_lbf = 4000.0.