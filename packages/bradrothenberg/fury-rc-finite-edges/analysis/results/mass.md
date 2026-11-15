# Weights, fuel and centre of gravity (estimate)

Bodies of the model with assumed densities. The structure is a representative layout, not a stressed design: read these as
first estimates. Stations are measured aft of the nose tip.

- Length 33.5 ft, span 24.85 ft, wetted area 830 ft2, enclosed volume 297 ft3
- Reference wing (input trapezoid to the centreline): area 143.9 ft2, aspect ratio 4.29, taper 0.165, mean aerodynamic chord 6.78 ft with its leading edge at station 15.84 ft

| Body | Volume [ft3] | Weight [lb] | Station of centroid [ft] | Height [in] | Basis |
|---|---:|---:|---:|---:|---|
| Skin | 8.30 | 829 | 19.71 | 6.4 | wetted area x skin thickness |
| Fuselage frames | 1.20 | 207 | 18.30 | 7.1 | 173 lb/ft3 |
| Wing spars | 0.31 | 54 | 18.24 | 3.7 | 173 lb/ft3 |
| Wing ribs | 0.17 | 30 | 18.96 | 3.7 | 173 lb/ft3 |
| Tail structure | 0.10 | 17 | 30.51 | 22.2 | 173 lb/ft3 |
| Engine | 13.50 | 650 | 27.24 | 13.7 | published dry weight, placed at the centroid of the envelope |
| Jet pipe | 0.15 | 42 | 32.10 | 13.7 | 277 lb/ft3 |
| Forward fuselage fuel | 32.88 | 1452 | 13.64 | 11.2 | usable fuel = cell volume x usable fraction |
| Centre fuselage fuel | 29.67 | 1310 | 17.95 | 13.2 | usable fuel = cell volume x usable fraction |
| Aft fuselage fuel | 41.49 | 1833 | 22.67 | 3.7 | usable fuel = cell volume x usable fraction |
| Wing fuel | 9.75 | 430 | 18.73 | 4.1 | usable fuel = cell volume x usable fraction |
| Mission systems bay | 19.34 | 0 | 6.39 | 8.9 | space, no weight assigned |
| Inlet duct air | 40.16 | 0 | 17.49 | 2.7 | space, no weight assigned |
| Landing gear (legs, wheels, tyres, doors) | 3.37 | 286 | 17.72 | -30.8 | assumed 4 % of the weight with full fuel |

| Total | Weight [lb] | Centre of gravity station [ft] | % of mean aerodynamic chord |
|---|---:|---:|---:|
| Structure (skin, frames, spars, ribs) | 1136 | 19.52 | 54 |
| Engine and jet pipe | 692 | 27.53 | 172 |
| Landing gear (assumed 4 % of full weight) | 286 | 17.72 | 28 |
| Usable fuel (749 US gal) | 5026 | 18.49 | 39 |
| Modelled items, no fuel | 2114 | 21.90 | 89 |
| Modelled items, full fuel | 7139 | 19.50 | 54 |

Fuel cells hold 851 US gal geometric volume; 88 % is counted usable: 5026 lb of JP-8.
This is the packing limit of the model: every fuselage bay between the tank bulkheads is filled except the landing gear bays, and so is the wing box.
A real aircraft gives more of that space to systems and weapons, so its fuel load is lower.
The landing gear is not weighed from its bodies: it is an assumed 4 % of the weight with full fuel, placed at the centroid of the gear bodies.
Systems, mission equipment, pylons and stores are not weighed, so the centre of gravity above is of the modelled items only.
With the reported 4000 lbf engine, thrust / weight of the modelled items at full fuel is 0.56.
The 5,000 lb maximum take-off weight often quoted for the Fury goes with the 20 ft by 17 ft size quoted for the earlier design; it is not used here
because the photographs give a 33.5 ft aircraft (reference/PROPORTIONS.md).

Assumptions: skin_density = 1600.0, structure_density = 2770.0, jet_pipe_density = 4430.0, fuel_density = 804.0, usable_fuel_fraction = 0.88, engine_weight_lb = 650.0, landing_gear_fraction = 0.04, engine_thrust_lbf = 4000.0.