# Lift and stability by vortex lattice (estimate)

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
| 0.0 | Conventional tail | 0.0745 | 18.99 | 47 | -0.120 | -0.236 |
| 0.0 | V-tail | 0.0730 | 18.83 | 44 | -0.176 | -0.340 |
| 0.6 | Wing alone | 0.0744 | 17.80 | 29 | -0.000 | -0.002 |
| 0.6 | Conventional tail | 0.0823 | 18.88 | 45 | -0.126 | -0.249 |
| 0.6 | V-tail | 0.0814 | 18.81 | 44 | -0.185 | -0.358 |

Centre of gravity of the modelled items (structure, engine, landing gear, fuel; no systems or stores) from analysis/results/mass.md:
full fuel at station 19.50 ft, no fuel at station 21.90 ft.
- Conventional tail: lattice neutral point is -7 % MAC aft of the full-fuel point and -43 % MAC aft of the no-fuel point (positive = stable, before the fuselage effect).
- V-tail: lattice neutral point is -10 % MAC aft of the full-fuel point and -45 % MAC aft of the no-fuel point (positive = stable, before the fuselage effect).