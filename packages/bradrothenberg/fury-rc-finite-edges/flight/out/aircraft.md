# Flight statement of the Fury model (estimates)

Everything here is an estimate from the shape of this model and public figures. No weight, thrust curve or aerodynamic coefficient of the real aircraft is published.

## Weights

| Item | Weight [lb] | Basis |
|---|---:|---|
| Structure | 1477 | modelled structure 1136 lb (analysis/results/mass.json, measured on the model) x 1.30 allowance |
| Engine and jet pipe | 692 | engine and jet pipe as in analysis/results/mass.json (engine weight assumed there from the public FJ44-4 figure) |
| Landing gear | 286 | weight model of the gear (analysis/results/mass.json) |
| Systems | 650 | assumption |
| Mission systems | 300 | assumption |
| **Empty** | **3404** | |
| Usable fuel, full | 5026 | what the modelled fuel cells hold (749 US gal); the real fuel load is not published |
| Stores | 812 | two AIM-120-class missiles on pylon launchers, as in the photographs the model was matched to |

| Case | Weight [lb] | Wing loading [lb/ft2] | Static thrust / weight | Ixx, Iyy, Izz [slug ft2] |
|---|---:|---:|---:|---|
| combat (50 % fuel, two missiles) | 6729 | 46.8 | 0.52 | 1708, 8473, 12035 |
| landing (15 % fuel, two missiles) | 4970 | 34.5 | 0.71 | 1262, 6258, 8889 |
| takeoff (full fuel, two missiles) | 9242 | 64.2 | 0.38 | 2346, 11638, 16529 |
| light (5,000 lb: the gross weight published for the original Fury design) | 5000 | 34.8 | 0.70 | 1269, 6296, 8942 |

ESTIMATE. The real weights are not published. The one public figure, 5,000 lb gross weight, was given for the original, smaller Fury design; it is carried as the "light" case.

## Reference and balance

Wing area 143.9 ft2, span 24.85 ft, mean aerodynamic chord 6.78 ft with its leading edge at station 15.84 ft.

| Point | Station [ft] | % of the mean chord |
|---|---:|---:|
| Neutral point, lattice of wing and tail (no body) | 18.99 | 47 |
| Neutral point with the fuselage moment (used) | 18.28 | 36 |
| Neutral point of the flow solution (line through all angles) | 17.73 | 28 |
| Centre of gravity flown (assumed) | 17.94 | 31 |
| Weight-model items, full fuel | 19.50 | 54 |
| Main wheels | 19.83 | |

Two estimates. Used in the flight model: lattice of wing and tail plus the fuselage moment by the Multhopp strip method. The flow solution of the whole aircraft (four angles, one grid) puts the neutral point further forward, and it moves aft with angle of attack. The flight model assumes a static margin, not a place: the centre of gravity is set a fixed fraction of the mean chord ahead of the estimate used, so with the flow-solution value the same flight behaviour needs the centre of gravity that much further forward.

The items of the weight model (structure, engine, gear, fuel; no systems) balance at station 19.5 ft with full fuel and the main wheels stand at 19.8 ft, both well aft of the flight centre of gravity assumed here (17.9 ft). Flown at the modelled balance the aircraft would be 18 % of the mean chord unstable against the estimated neutral point. Either the real neutral point is further aft than this shape gives, or the real mass is further forward, or the real aircraft flies unstable on its flight control system. Not resolved.

## Engine

Thrust 3,790 lbf sea-level static: public figure of the FJ44-4M (Aero L-39NG data); the FJ44-4M is the engine publicly named for the YFQ-44A. Lapse with speed and height: Mattingly, Heiser and Pratt high-bypass form with the Mach term reduced to 0.30 for a bypass ratio of 3 to 4 (ASSUMPTION), flat rated to a throttle ratio of 1.04. Installation: (1 - 1.35 x (1 - recovery)) x offtake x nozzle = 0.926 with an assumed inlet recovery of 0.97. No afterburner. Uncertainty about plus or minus 15 % at speed and height.

| Mach | Sea level [lbf] | 15,000 ft [lbf] | 30,000 ft [lbf] |
|---:|---:|---:|---:|
| 0.0 | 3510 | 1981 | 1042 |
| 0.2 | 3125 | 1764 | 928 |
| 0.4 | 3176 | 1792 | 943 |
| 0.6 | 3232 | 1940 | 1021 |
| 0.8 | 3301 | 2209 | 1163 |
| 0.9 | 3342 | 2388 | 1261 |

## Lift and drag (clean, with the two missiles)

Zero-lift drag: equivalent skin friction 0.0030 on the wetted area of the model (830 ft2, measured). Drag due to lift: 1 / (pi AR) with a leading-edge suction schedule, the rest of the lift force tilted back by the angle of attack. Compressibility: Korn equation with Lock's fourth-power rise. Stores, gear, flap: drag areas and the plain-flap profile drag rule as stated in ASSUME. The flow solution is not used for drag; it gives less zero-lift drag (0.0099 against 0.0173) and about twice the drag due to lift (CD = CD0 + 0.20 CL2 against about 0.09 CL2 here), see the sensitivity in turn.md.

| Mach | Lift slope [per deg] | Usable CLmax | Angle of the limiter [deg] | Zero-lift drag | Best lift/drag (trimmed) |
|---:|---:|---:|---:|---:|---:|
| 0.3 | 0.0762 | 1.10 | 15.7 | 0.0201 | 12.0 |
| 0.5 | 0.0796 | 1.10 | 15.1 | 0.0201 | 12.1 |
| 0.7 | 0.0861 | 0.97 | 12.5 | 0.0201 | 12.2 |
| 0.8 | 0.0916 | 0.87 | 10.7 | 0.0201 | 12.1 |
| 0.9 | 0.1003 | 0.78 | 9.0 | 0.0216 | 9.7 |

## Derivatives at Mach 0.5 (per rad, lattice with the stated factors)

| | Value | | Value |
|---|---:|---|---:|
| cl_q | 9.1186 | cm_q | -9.1676 |
| cl_de | 1.3207 | cm_de | -2.2039 |
| cl_df | 1.2586 | cm_df | -0.1965 |
| cd_de1 | 0.1715 | cd_de3 | 0.5477 |
| cd_de2 | 0.0200 | cd_df1 | 0.2147 |
| cd_df3 | 0.1351 | cd_df2 | 0.1069 |
| cd_dr2 | 0.0200 | cd_gear | 0.0222 |
| cm_gear | -0.0102 | cy_b | -0.4445 |
| cy_p | 0.0046 | cy_r | 0.2863 |
| cy_da | -0.0654 | cy_dr | 0.1059 |
| cll_b0 | -0.0190 | cll_b1 | -0.0817 |
| cll_p | -0.3434 | cll_r0 | 0.0345 |
| cll_r1 | 0.1163 | cll_da | 0.2172 |
| cll_dr | 0.0152 | cn_b0 | 0.0468 |
| cn_b1 | -0.0239 | cn_p0 | 0.0124 |
| cn_p1 | -0.2070 | cn_r0 | -0.1478 |
| cn_r1 | 0.0447 | cn_da | 0.0226 |
| cn_dr | -0.0589 | stab_k1 | 0.9500 |
| stab_k2 | 0.4500 | stab_break | 0.2443 |
| flap_k1 | 0.8500 | flap_k2 | 0.3750 |
| flap_break | 0.1745 |  |  |