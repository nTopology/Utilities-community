# Fury notebook: a guide for someone new to nTop

Notebook: `fury-rc-finite-edges.ntop` (nTop 6.3). It is a parametric model of an Anduril YFQ-44A Fury class
aircraft: outer mold line matched to public photographs, inlet duct, landing gear, skin, frames, spars and ribs,
an engine envelope and fuel. Read this once, then open the notebook and read it top to bottom. The sections are in the
order the aircraft is built, and no block uses anything defined below it.

## 1. What you see when it opens

The outside is shown: **Skin**, **Air data boom**, **Panel lines**, the paint and the markings, the landing gear (down)
and the external fittings (pylons, launch rails, missile-sized dummies, antennas). The other bodies are in section
**40 Bodies**, hidden. Click the eye beside a body to show it. Hide the skin and the paint to see frames, spars, ribs,
engine and fuel.

Every section is collapsed and starts with a description. Open them one at a time.

| Section | What is in it |
|---|---|
| 00 Coordinates | X, Y, Z: the position of every point. X aft from the nose tip, Y to the right wing, Z up |
| 01 to 06 Inputs | The numbers you are meant to change (ft, in, deg, %) and three switches: tail type, landing gear, wing stores |
| 07 Derived dimensions | The inputs converted to metres and radians. Nothing to edit |
| 08 Reference coordinates | X, \|Y\|, Z divided by the size inputs, so one set of curves serves every size |
| 10 Fuselage guide curves | Curves of fuselage dimensions against station: half width, crown, chine, keel, belly, duct |
| 11 Fuselage lofts | Three lofted surfaces: upper, underside (continues aft as the duct roof), lower |
| 12 Inlet, duct and nozzle | Lip surface, splitter plate, diverter slot, duct air, jet pipe |
| 13 Fuselage | The three lofts put together and hollowed by the duct |
| 14 Wing, 15 Tail | The lifting surfaces and the tail switch |
| 16 Exterior | Fuselage + wing + tail with fillets: the outer mold line |
| 20 Structure | Skin shell, frames, bulkheads, spars, ribs |
| 21 Panel lines | The panel line pattern and the grooves it cuts in the skin |
| 22 Paint and markings | Dark band, lettering, national insignia, formation lights |
| 30 Engine and systems, 31 Fuel | Engine envelope with spinner, jet pipe, boom, mission bay, fuel cells |
| 32 Landing gear | Legs, struts, wheels and tyres, the bays cut into the underside, the doors |
| 33 External fittings | Pylons, launch rails, missile-sized dummies, flap actuator fairings, dorsal scoop, antennas, air data probes |
| 40 Bodies | The finished bodies |
| 99 Checks | The model evaluated at six points, to compare with the numbers computed outside nTop |

## 2. The one idea behind everything: a shape is a field

In nTop an implicit body is a **field**: a formula that gives a number at every point in space. The number is
negative inside the part, zero on its surface and positive outside. That is all a body is.

Three consequences that the whole notebook uses:

- **Joining and cutting is min and max.** `min(A, B)` is A and B together. `max(A, B)` is the part common to both.
  `max(A, -B)` is A with B cut away. A smooth min gives a fillet.
- **Offsetting is adding.** `A + 0.12 in` is A shrunk by 0.12 in. The skin is `max(Exterior, -(Exterior + skin thickness))`.
- **Moving a part is changing the coordinates you feed it.** Using `|Y|` in place of `Y` mirrors the part to both sides.

## 3. The two building blocks

**Guide curve** (section 10). A smooth curve of one dimension against fuselage station, for example
"Fuselage half width". It is a spline through a short list of control values. Feed it the reference station
and it returns the half width at that station as a field. To reshape the fuselage, edit the control values of a guide.

**Spline DF section** (sections 11, 12, 14, 15). nTop's Spline DF block gives the distance to a 2D spline drawn
through control points. Here the control points are not constants: each one is built from guide curves, so the
section changes shape as you move along the aircraft. One block lofts a whole surface.

Example, the upper fuselage loft. In the cross-section plane the spline runs from the crown on the centreline
out to the chine. Its control points are (half width x a, chine height + (crown - chine) x b) with fixed
numbers a and b for each point, and half width, chine and crown come from guides. The field is negative below
the curve, so "Fuselage upper loft" is a solid that fills everything under the crown line.

The fuselage is then three such solids combined (section 13):

```
Fuselage = max( below the upper loft,
                above the lower side,        # forebody underside in front, inlet cowl behind the lip
                behind the nose, ahead of the nozzle )
           with the duct air and the jet pipe cut away
```

"Solid on each side, then keep the common part" is the pattern. It never needs a closed curve, and it stays
robust when you change the inputs.

## 4. Inlet and duct

- The **forebody underside** loft carries on aft inside the fuselage as the **duct roof**. This is how the real
  inlet works: the forebody is the upper wall of the inlet.
- The **lower fuselage** loft is the cowl. Its section is a V-shaped hull: side walls that lean in at about 45 deg from
  the chine down to a corner at about half the breadth. At the inlet the bottom falls from that corner to a keel on the
  centreline (about 11 deg); further aft the keel fades into a flat belly. Seen from the front the inlet opening is a
  wide, shallow hexagon, as in the head-on photographs.
- The cowl is cut at the front by the **inlet lip surface**: a face that leans, so the top of the opening is well
  ahead of the bottom lip. "Inlet lip sweep" turns each half of the face back from the centreline, so the face is two
  flat facets with a crease on the centreline. With 7 deg the upper lip comes out straight across in plan.
- The **duct air** is the space below the roof, above the **duct floor** loft and one lip thickness inside the cowl.
  It runs to the round engine face. Its floor heights were solved so the duct area is smallest just behind the
  lip (the throat) and grows smoothly to the engine face (`tools/tune_duct.py`).
- The **splitter plate** is the top wall of the cowl and the upper lip of the inlet: a blunt lip that lies in the
  inlet face with the others. It is a shallow V ("Upper lip V angle"), lowest on the centreline, where it lies one
  **diverter height** below the forebody underside. The forebody underside is rounder than the plate, so the slot
  between them is taller toward the sides. The slot carries the slow boundary-layer air of the forebody past the inlet
  instead of into the engine. Behind the lip a swept **diverter wedge** closes the slot, so it opens to the sides under
  the chine, and the plate runs into the cowl there.
  In the notebook: "Height above the splitter plate" is the top of the plate; the slot is the air below the forebody
  underside and above the plate, ahead of the wedge; the duct roof starts one plate thickness below the top of the plate
  and changes to the underside loft aft of the slot.
- The **jet pipe** is a cone from the engine to the nozzle exit.

## 5. Wing and tail: one recipe, used four times

Each lifting panel (wing, horizontal tail, fin, V-tail) is built the same way:

1. A **span coordinate** s that runs along the panel and a **normal coordinate** n, the distance from the panel's
   chord plane. Dihedral or cant is a rotation of (\|Y\|, Z) into (s, n).
2. Leading-edge station, chord and thickness are straight lines of s (root value to tip value).
3. The chord fraction u = (X - leading edge) / chord, and one airfoil Spline DF gives the half thickness at u.
   The panel is `|n| - thickness x half-thickness curve`, cut at the tip.

**Tail switch.** Input "Tail type" is 0 for the conventional tail (one fin, two horizontal tails) and 1 for the
V-tail. Both tail sets are always defined. The switch adds 100 m to the field of the set that is not selected,
which makes it positive everywhere, so it disappears from every body (skin, structure, rudder gap).

## 6. Landing gear and external fittings

The landing gear (section 32) is built from four small shapes: a **rod** (the distance to a straight line between two
points, minus a radius), a **ball**, a **disc** and a **wheel**. Every end point is a formula of the gear inputs and the
fuselage size, so the gear follows when you move a wheel, change the track or the ground line.

- **Nose gear**: one leg at the front of its bay, a one-sided fork with the wheel beside it, torque links behind the leg,
  a drag brace aft into the bay.
- **Main gear**: a leg from the lower fuselage that leans outboard to a single wheel, a folding strut forward into the
  bay, a side brace to the keel, torque links, brake.
- **Bays**: boxes with a sawtooth outline in plan, cut into the outer mold line under the inlet duct. They stop a wall
  thickness below the duct. Fuel keeps out of them.
- **Doors**: flat plates hanging open from their hinge lines, a pair on the nose bay, an inner and an outer door on each
  main bay. The outer main doors carry the landing lights.
- **The switch.** "Landing gear" = 0 adds 100 m to the gear, the doors and the bays, so they all vanish and the
  underside closes. Only the door outlines stay as panel lines.

What it is not: the gear does not fold. The legs, wheels and bays are sized and placed from photographs; whether the
wheels fit in the bays when retracted was not worked out, and the nose bay under the duct is only a few inches deep.

The external fittings (section 33) are simple shapes placed at stations read from the photographs: a pylon and launch
rail under each wing with a plain missile-sized body (12 ft long, 7 in diameter), the flap actuator fairings, the small
scoop on the spine, blade antennas and the two air data probes under the nose chine. "Wing stores" = 0 gives the clean wing.

## 7. Panel lines, paint and markings

These are **patterns**. A pattern is a field drawn in a flat view (side view, plan view, or the plane of a wing panel)
that does not change along the third direction, so it goes straight through the aircraft like a cookie cutter.
It becomes something you can see where it meets a thin layer on the outer mold line:

```
Panel grooves   = max( Panel line pattern, -(Outer mold line + groove depth) )      # cut from the skin
Paint layer     = max( pattern, Outer mold line - film, -(Outer mold line + film) ) # a film on the surface
```

- **Panel lines**: fuselage breaks at the frame stations, wing and tail lines along the spars and ribs (they move with
  the spar inputs), door and hatch outlines as rectangles. A line is `|coordinate - position| - half width`.
- **Dark band**: a region of the side view above a stepped lower edge.
- **Lettering**: every letter is a few straight strokes; the text is the distance to the nearest stroke minus half the
  stroke width. Side lettering multiplies the reading direction by the side of the aircraft (+1 right, -1 left), so it
  reads correctly from outside on both sides.
- **National insignia**: a disc with a five-pointed star cut out and two bars, on the upper left and lower right wing.
  It follows the wing planform inputs.

The paint layers are 0.02 in thick films, drawn so they show in the viewport. To export the outside as one mesh, use
"Outer mold line" as before.

## 8. Things to try

| You want to | Change |
|---|---|
| Switch to the V-tail | 03 Inputs: Tail type = 1 |
| A bigger or smaller aircraft with the same shape | 01 Inputs: Fuselage length. Wing and tail dimensions are separate inputs in ft, so scale them too |
| A fatter or flatter fuselage | 01 Inputs: Fuselage width scale, Fuselage height scale |
| More sweep, span, taper | 02 Inputs: the wing planform inputs |
| Move the wing | 02 Inputs: Wing apex station, Wing height |
| V-tail angle | 03 Inputs: V-tail cant angle |
| Gear up, clean wing | 06 Inputs: Landing gear = 0, Wing stores = 0 |
| A wider track, a longer wheelbase, a taller stance | 06 Inputs: Main gear track, the two gear stations, Ground line |
| Inlet further forward or aft | 04 Inputs: Inlet lip station |
| A taller or shorter diverter slot | 04 Inputs: Diverter height |
| A thicker upper lip, or one that stands ahead of the inlet face | 04 Inputs: Splitter plate thickness, Splitter plate overhang |
| A flat inlet face (no crease), a more upright inlet face | 04 Inputs: Inlet lip sweep = 0, Inlet face lean |
| A flatter or steeper V in the upper lip | 04 Inputs: Upper lip V angle |
| Wider or deeper panel lines | 05 Inputs: Panel line width, Panel line depth |
| Thicker skin or webs | 05 Inputs |
| Reshape the fuselage itself | 10 Fuselage guide curves: edit the control values of a guide |

After a change nTop recomputes every body. To check sizes use a Bounding Box or Mass Properties block on a body
in section 40.

## 9. Practical notes

- **Meshing.** The skin is 0.12 in thick. To export or render the outside, mesh "Outer mold line" (section 16),
  not the skin. A tolerance of 0.4 in (10 mm) is right for the whole aircraft; 0.12 in on the whole exterior
  gives about 40 million triangles and takes an hour.
- **Flow body.** For CFD use the outer mold line with inlet and nozzle faired over; the Python model builds it with
  `Airframe.exterior(opened=False)` in `model/oml.py`.
- **Limits.** The fuselage guides are drawn for the reference aircraft. Length, width and height scales stretch
  them; inputs far from the Fury values (for example a wing apex ahead of the inlet) still compute but may not
  look like an aircraft. The engine envelope is a fixed size and does not scale with the fuselage.
- **Structure and fuel are a representative layout**, not a stressed design: frame stations, spar positions and
  tank limits are sensible places, chosen by eye. Fuel is the packing limit of the bays.
- **Landing gear and fittings are for looks and layout**: placed and sized from photographs, good to a few inches.
  No loads, no retraction.
- **Units.** Inputs are in ft, in, deg and %. Inside, the notebook works in metres.

## 10. Where the notebook comes from

The notebook is generated. The model is written once in Python (`model/`), which can evaluate the same fields
directly (for previews, photo matching and analysis) and write them as an nTop notebook:

```
model/design.py      the input table
model/oml.py         guides, lofts, inlet, wing, tail, exterior
model/aircraft.py    skin, structure, engine, fuel, the list of bodies
model/gear.py        landing gear, bays, doors
model/fittings.py    pylons, rails, dummies, fairings, scoop, antennas
model/livery.py      panel lines, paint, markings
tools/build_native.py   writes fury-rc-finite-edges.ntop with the installed nTop (about 10 minutes)
```

You do not need Python to use the notebook. If you change a guide in Python, run `tools/build_native.py` to
get a new notebook. The notebook was checked against the Python model by meshing it in nTop and evaluating the
Python field at every mesh vertex (results in `publication-checks.json`).
