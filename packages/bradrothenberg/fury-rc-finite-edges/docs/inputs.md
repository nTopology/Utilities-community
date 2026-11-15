# Inputs of the notebook

Every input is a variable in sections 01 to 06 of `fury-rc-finite-edges.ntop`. Values are the Fury match.


## 01 Inputs | Fuselage

| Input | Value | What it does |
|---|---:|---|
| Fuselage length [ft] | 33.5 | Nose tip to nozzle exit. Every fuselage station scales with it. |
| Fuselage width scale [-] | 1 | Multiplies every fuselage half width. 1 = as the reference aircraft. |
| Fuselage height scale [-] | 1 | Multiplies every fuselage height and depth. 1 = as the reference aircraft. |

## 02 Inputs | Wing

| Input | Value | What it does |
|---|---:|---|
| Wing span [ft] | 24.85 | Tip to tip. |
| Wing root chord [ft] | 9.94 | Chord on the aircraft centreline (the wing is continued to the centreline inside the body). |
| Wing tip chord [ft] | 1.64 | Chord at the tip. |
| Wing leading-edge sweep [deg] | 31 | Sweep of the leading edge, positive aft. |
| Wing apex station [% length] | 38.8 | Where the leading edge would meet the centreline, as a percentage of the fuselage length. |
| Wing height [in] | 5.5 | Height of the wing chord plane above the fuselage reference line. The chine is 4 in above that line, so the chine runs into the wing leading edge. |
| Wing dihedral [deg] | -1.5 | Positive tips up. |
| Wing thickness at root [% chord] | 8 | Maximum thickness of the section on the centreline. |
| Wing thickness at tip [% chord] | 5 | Maximum thickness of the section at the tip. |

## 03 Inputs | Tail

| Input | Value | What it does |
|---|---:|---|
| Tail type (0 = conventional, 1 = V-tail) | 0 | 0 builds a fin and two horizontal tails. 1 builds two canted V-tail panels instead. |
| Horizontal tail span [ft] | 12.73 | Tip to tip (conventional tail). |
| Horizontal tail root chord [ft] | 6.2 | Chord on the centreline. |
| Horizontal tail tip chord [ft] | 1.47 | Chord at the tip. |
| Horizontal tail leading-edge sweep [deg] | 34 | Positive aft. |
| Horizontal tail apex station [% length] | 80.7 | Leading edge on the centreline, percentage of the fuselage length. |
| Horizontal tail height [in] | 8.9 | Height of the tail plane above the fuselage reference line. |
| Horizontal tail dihedral [deg] | 0 | Positive tips up, negative for anhedral. |
| Fin height [ft] | 4.87 | From the fin root line to the fin tip (conventional tail). |
| Fin root chord [ft] | 4.97 | Chord on the fin root line. |
| Fin tip chord [ft] | 2.12 | Chord at the fin tip. |
| Fin leading-edge sweep [deg] | 45 | Positive aft. |
| Fin apex station [% length] | 80.5 | Leading edge at the fin root line, percentage of the fuselage length. |
| Fin root height [in] | 21.2 | Height of the fin root line above the reference line. Keep it inside the body. |
| V-tail cant angle [deg] | 47 | Angle of each V-tail panel above the horizontal. |
| V-tail panel length [ft] | 6.59 | Root to tip along the panel (V-tail). |
| V-tail root chord [ft] | 5.81 | Chord on the centreline. |
| V-tail tip chord [ft] | 1.62 | Chord at the tip. |
| V-tail leading-edge sweep [deg] | 38 | Positive aft, measured in the plane of the panel. |
| V-tail apex station [% length] | 80.5 | Leading edge on the centreline, percentage of the fuselage length. |
| V-tail root height [in] | 10.1 | Height of the V vertex above the reference line. Keep it inside the body. |
| Tail thickness [% chord] | 5 | Maximum thickness of every tail section. |
| Trailing-edge thickness [in] | 0.25 | Finite thickness of every wing and tail trailing edge. |

## 04 Inputs | Inlet, duct and engine

| Input | Value | What it does |
|---|---:|---|
| Inlet lip station [% length] | 29.5 | Station of the lower inlet lip on the centreline, percentage of the fuselage length. |
| Inlet face lean [deg] | 48 | The inlet face leans forward from the lower lip up to the splitter plate by this angle from vertical. |
| Inlet lip sweep [deg] | 7 | Turns each half of the inlet face back from the centreline, so the face is two facets with a crease on the centreline. With the leaning face and the V-shaped upper lip, about 7 deg makes the upper lip straight across in plan (estimated from photograph 37). |
| Upper lip V angle [deg] | 6 | The upper lip (the splitter plate) is a shallow V, lowest on the centreline. This is the rise of each half from level (estimated from photograph 37). |
| Diverter height [in] | 1.5 | Gap between the forebody underside and the splitter plate: the slot that carries the forebody boundary layer past the inlet. |
| Splitter plate thickness [in] | 1 | Thickness of the splitter plate: the top wall of the cowl and the upper lip of the inlet. |
| Splitter plate overhang [in] | 0 | How far the splitter plate (the upper lip) stands ahead of the inlet face. 0 on the aircraft: all the lips lie in the face. |
| Diverter wedge sweep [deg] | 50 | Sweep of the wedge that closes the diverter slot behind the inlet lip and turns the boundary layer out to the sides. |
| Inlet lip thickness [in] | 1 | Wall between the outer cowl and the duct at the lip. |
| Nozzle exit diameter [in] | 16.8 | Inner diameter of the exhaust nozzle at the exit. |

## 05 Inputs | Structure and fuel

| Input | Value | What it does |
|---|---:|---|
| Skin thickness [in] | 0.12 | Thickness of the outer skin. Representative, not stressed. |
| Frame and spar web thickness [in] | 0.2 | Thickness of frames, ribs and spar webs. Representative, not stressed. |
| Wing front spar [% chord] | 18 | Front spar position along the local chord. |
| Wing rear spar [% chord] | 68 | Rear spar position along the local chord. |
| Fuel tank wall clearance [in] | 1 | Gap between a fuel tank and the structure or skin around it. |
| Panel line width [in] | 0.25 | Width of the grooves that divide the skin into panels. Drawn wider than a real gap so it shows. |
| Panel line depth [in] | 0.05 | Depth of the panel grooves below the outer surface. Keep it below the skin thickness. |

## 06 Inputs | Landing gear and stores

| Input | Value | What it does |
|---|---:|---|
| Landing gear (1 = down, 0 = retracted) | 1 | 1 builds the gear, opens the bays and hangs the doors. 0 removes the gear and closes the bays. |
| Nose gear station [% length] | 35.2 | Station of the nose wheel axle. |
| Main gear station [% length] | 59.2 | Station of the main wheel axles. |
| Main gear track [in] | 67.5 | Distance between the centres of the two main wheels. |
| Ground line below the reference line [in] | 47 | How far the ground is below the fuselage reference line with the aircraft standing on its wheels. Sets the leg lengths. |
| Main tyre diameter [in] | 19 | Outer diameter of a main tyre. The width follows. |
| Wing stores (1 = pylons, rails and missiles, 0 = clean wing) | 1 | 1 hangs a pylon with a launch rail and a missile-sized dummy under each wing, as in most photographs. 0 leaves the wing clean. |
| Nose tyre diameter [in] | 14.5 | Outer diameter of the nose tyre. The width follows. |