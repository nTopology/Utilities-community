# Notebook walkthrough

Open a copy of a notebook in nTop. The saved notebooks have the final body visible and sections collapsed. Expand **Inputs**, **Calculations**, **Construction**, and **Checks** as needed; the large **Expressions** section contains generated intermediate arithmetic. Labels below are exact saved block names, not suggested future features.

## 1. Enclosure: geometry and development are different models

Open `models/enclosure.ntop`.

1. **Inputs**: `Thickness`, `Inside bend radius`, `K factor`, `Outside length`, `Outside width`, `Outside height`, `Diagonal seam gap`, `Relief root radius`, `Mounting hole diameter`.
2. **Calculations**: highlight `Geometric midsurface radius` and `90 degree bend allowance`. The former uses Ri+t/2; the latter uses (pi/2)(Ri+K*t). Changing K should change development, not the formed bend.
3. **Construction**: follow `Circular root exclusion`, `Relieved planar floor`, `Y +1 45 degree trim`, and `Y +1 mitered flange`. The other three flanges use the same construction pattern.
4. **Construction/Expressions**: trace `Y +1 developed field` to `Y +1 developed flange`, then `Flat enclosure blank`. The formed field is evaluated under a fold map; this is not an unrelated rectangular blank.
5. **Checks**: inspect `CHECK bend 45 inner`, `CHECK bend 45 mid`, `CHECK bend 45 outer`, `CHECK seam 1 1 90 center`, and `CHECK root 1 1 void`. These sample geometry; they do not certify every point or a cutting process.

Try changing K from 0.42 to 0.50 on a copy and compare `90 degree bend allowance`. Return to the baseline before comparing with the bundled evidence. This is a suggested exercise, not an additional native run in this publication.

Nominal envelope 152.4 x 101.6 x 50.8 mm, thickness 1.016 mm, inside radius 1.5 mm, 0.5 mm normal seam gap and R0.5 relief roots. The 45-degree through-thickness edges require bevel preparation; this developed solid is not a conventional perpendicular-cut blank.

The report's corner close-up uses a fresh nTop Automate export with a 0.01 mm mesh setting and an offscreen PyVista/VTK render. The display crop lies outside the image boundary. Interpolated surface normals improve lighting while split normals preserve sharp edges; no mesh vertices or source geometry are smoothed. This is not an nTop viewport screenshot. See `evidence/corner-render.json` for hashes and settings.

## 2. Corrugation: encode the repeated section once

Open `models/corrugated-shield.ntop`. Highlight `Thickness`, `Inside bend radius`, `Midsurface radius`, `Slope tangent`, `Crest tangent`, `Valley tangent`, `Corrugated stock section`, and `Corrugated stock`. A line-and-arc profile supplies five waves with twenty 60-degree bends; one extrusion preserves the common section.

Follow `Slotted stock` and `Crest pierced stock` to `Final Corrugated mounting shield`. The six mounting slots and five crest holes are late cuts. `CHECK section 7 face A`, `CHECK section 7 stock`, and `CHECK section 7 face B` sample thickness. `CHECK Crest void 0` samples a pierced hole. Five waves and the bend angles are compiled construction choices in this saved version, not exposed count/angle inputs.

Nominal thickness 1.2 mm and inside radius 1.6 mm. The separate FE example forms unpierced stock before the eleven openings: it does not solve the piercing operation. The FE final state need not coincide with the target CAD surface.

## 3. Housing: use fields to carry a profile around a perimeter

Open `models/stepped-housing.ntop`. Highlight `Two-level meridian meridian` (the saved label repeats the word), `Two-level meridian`, `X field`, `Y field`, `Z field`, and `Stepped housing stock`. A signed coordinate map carries the two-step cross-section around a rounded rectangular perimeter.

For the closed embosses, follow `Closed bead master meridian`, `Bead floor opening 0`, `Closed bead 0`, `Opened bead stock`, and `Beaded stock`. The original floor under each patch is removed; a raised solid rib over an intact floor would not represent this sheet feature. Inspect `CHECK bead 0 underside`, `CHECK bead 0 cavity`, and `CHECK bead 0 closed end`.

The 3-degree wall draft is compiled into the analytic meridian (87-degree wall direction); it is not a named Draft input. `CHECK draft flank 2 station 0.25 face -1` and related samples inspect that revision. They are geometric checks, not proof of release under friction or forming load. The nominal target uses constant 1.2 mm stock. The external FE result includes computed thinning and is a separate representation.

## What is outside these notebooks

Tool surface envelopes, release sweeps, shell meshing, contact, material plasticity, blank-holder force and unloading are external script/solver stages. The archive includes recorded evidence and illustrations, not an integrated solver installer or the full FE execution environment. No automatic springback-compensated die or stamped-blank inverse solution is claimed.

## Compatibility

The native file headers record development version 6.1.0. These are recorded API-study saves, not a compatibility test across public releases. The package's 6.1+ catalog value reflects that header; opening on a particular public build is unverified. Recipes are included for inspection and API-enabled reconstruction. The report and calculators need only a modern browser. No prerelease executable is distributed.
