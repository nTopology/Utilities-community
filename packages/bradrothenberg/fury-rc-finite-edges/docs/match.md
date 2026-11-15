# How well the model matches the photographs

Each photograph is mapped into the model frame from a few picked points (nose tip, nozzle centre, wing tips), and the model
silhouette is drawn on it. Orange: outline of the model. Cyan: outline of the aircraft found in the photograph (against the sky).
Overlap is intersection over union of the two silhouettes; the outline distance is given in percent of the fuselage length
(1 % of length = 4 in). Landing gear, missile, pylon and nose boom are in the photographs and not in the model outline, so they
are left out of the score where a score window is set (`docs/match-views.json`).

| View | Photograph | Overlap | Outline distance, median | Outline distance, 90 % of the outline within |
|---|---|---:|---:|---:|
| plan_01 | `01_plan_underside_flight_gearup_anduril.jpg` | 0.909 | 0.28 % | 1.56 % |
| side_07 | `07_side_flight_gear_down_aim120_1001_usaf.jpg` | 0.976 | 0.00 % | 0.33 % |

## Side view

![side](img/match-side-07.jpg)

## Plan view (underside)

_The plan-view overlay is drawn on a company press photograph and is not redistributed here; the numbers are in the table above._

The plan photograph is an oblique view, so the near fuselage side and the fin show beside the planform; that is most of the
difference in the plan numbers.

## Checked by eye, not scored

- Front view (photographs 12 to 14): arch upper section, chine overhanging the cowl, wide shallow inlet, 1.5 deg anhedral.
- Inlet (photographs 07, 18, 19): lower lip station, chevron lower lip, side walls leaning forward, the pointed splitter plate under the
  forebody and the diverter slot above it. The slot height and the plate thickness are estimates.
- Paint and markings (photographs 04, 05, 06, 07, 17): two greys, designation, tail code, serial, insignia. Positions from the photographs;
  the lettering is a plain stroke font, panel lines are a representative layout at the frames, spars and doors.
- Not modelled: landing gear (door outlines only), pylons, antennas, the dorsal sensor fairing.

Measured proportions and how the scale was found: `docs/proportions.md`.