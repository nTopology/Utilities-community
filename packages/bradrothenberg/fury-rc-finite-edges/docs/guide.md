# Fury notebook: a guide for someone new to nTop

Notebook: `fury-rc-finite-edges.ntop` (nTop 6.3). It is a parametric model of an Anduril YFQ-44A Fury class
aircraft: outer mold line matched to public photographs, inlet duct, skin, frames, spars and ribs, an engine
envelope and fuel. Read this once, then open the notebook and read it top to bottom. The sections are in the
order the aircraft is built, and no block uses anything defined below it.

## 1. What you see when it opens

The outside is shown: **Skin**, **Air data boom**, **Panel lines**, the paint and the markings. Twelve more bodies are in
section **40 Bodies**, hidden. Click the eye beside a body to show it. Hide the skin and the paint to see frames, spars,
ribs, engine and fuel.

Every section is collapsed and starts with a description. Open them one at a time.

| Section | What is in it |
|---|---|
| 00 Coordinates | X, Y, Z: the position of every point. X aft from the nose tip, Y to the right wing, Z up |
| 01 to 05 Inputs | The numbers you are meant to change (ft, in, deg, %) |
| 06 Derived dimensions | The inputs converted to metres and radians. Nothing to edit |
| 07 Reference coordinates | X, \|Y\|, Z divided by the size inputs, so one set of curves serves every size |
| 10 Fuselage guide curves | Curves of fuselage dimensions against station: half width, crown, chine, keel, belly, duct |
| 11 Fuselage lofts | Three lofted surfaces: upper, underside (continues aft as the duct roof), lower |
| 12 Inlet, duct and nozzle | Lip surface, splitter plate, diverter slot, duct air, jet pipe |
| 13 Fuselage | The three lofts put together and hollowed by the duct |
| 14 Wing, 15 Tail | The lifting surfaces and the tail switch |
| 16 Exterior | Fuselage + wing + tail with fillets: the outer mold line |
| 20 Structure | Skin shell, frames, bulkheads, spars, ribs |
| 21 Panel lines | The panel line pattern and the grooves it cuts in the skin |
| 22 Paint and markings | Dark band, lettering, national insignia, formation lights |
| 30 Engine and systems, 31 Fuel | Engine envelope, jet pipe, boom, mission bay, fuel cells |
| 40 Bodies | The 19 finished bodies |
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
- The **lower fuselage** loft is the cowl. It is cut at the front by the **inlet lip surface**: a chevron lower lip
  (swept back from the centreline) with side walls that lean forward up to the underside.
- The **duct air** is the space below the roof, above the **duct floor** loft and one lip thickness inside the cowl.
  It runs to the round engine face. Its floor heights were solved so the duct area is smallest just behind the
  lip (the throat) and grows smoothly to the engine face (`tools/tune_duct.py`).
- The **splitter plate** is the upper lip of the inlet. It is an arrowhead plate with its point on the centreline, one
  **diverter height** below the forebody underside. The slot between plate and forebody carries the slow boundary-layer
  air of the forebody past the inlet instead of into the engine. Behind the lip a swept **diverter wedge** closes the
  slot, so it opens to the sides under the chine, and the plate runs into the cowl there.
  In the notebook: the underside loft gives the distance below the forebody; the slot is where that distance is between 0
  and the diverter height, the plate is the next layer down, and the duct roof starts below the plate.
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

## 6. Panel lines, paint and markings

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

## 7. Things to try

| You want to | Change |
|---|---|
| Switch to the V-tail | 03 Inputs: Tail type = 1 |
| A bigger or smaller aircraft with the same shape | 01 Inputs: Fuselage length. Wing and tail dimensions are separate inputs in ft, so scale them too |
| A fatter or flatter fuselage | 01 Inputs: Fuselage width scale, Fuselage height scale |
| More sweep, span, taper | 02 Inputs: the wing planform inputs |
| Move the wing | 02 Inputs: Wing apex station, Wing height |
| V-tail angle | 03 Inputs: V-tail cant angle |
| Inlet further forward or aft | 04 Inputs: Inlet lip station |
| A taller or shorter diverter slot | 04 Inputs: Diverter height |
| A longer or more swept splitter plate | 04 Inputs: Splitter plate apex station, Splitter plate sweep |
| Wider or deeper panel lines | 05 Inputs: Panel line width, Panel line depth |
| Thicker skin or webs | 05 Inputs |
| Reshape the fuselage itself | 10 Fuselage guide curves: edit the control values of a guide |

After a change nTop recomputes every body. To check sizes use a Bounding Box or Mass Properties block on a body
in section 40.

## 8. Practical notes

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
- **Units.** Inputs are in ft, in, deg and %. Inside, the notebook works in metres.

## 9. Where the notebook comes from

The notebook is generated. The model is written once in Python (`model/`), which can evaluate the same fields
directly (for previews, photo matching and analysis) and write them as an nTop notebook:

```
model/design.py      the input table
model/oml.py         guides, lofts, inlet, wing, tail, exterior
model/aircraft.py    skin, structure, engine, fuel, the list of bodies
model/livery.py      panel lines, paint, markings
tools/build_native.py   writes fury-rc-finite-edges.ntop with the installed nTop (about 4 minutes)
```

You do not need Python to use the notebook. If you change a guide in Python, run `tools/build_native.py` to
get a new notebook. The notebook was checked against the Python model by meshing it in nTop and evaluating the
Python field at every mesh vertex (results in `publication-checks.json`).
