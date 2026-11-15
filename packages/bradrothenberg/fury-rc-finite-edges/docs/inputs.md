# Inputs of the notebook

Every input is a variable in sections 01 to 05 of `fury-rc-finite-edges.ntop`. Values are the Fury match.


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
| Wing height [in] | 4 | Height of the wing chord plane above the fuselage reference line (the chine). |
| Wing dihedral [deg] | -1.5 | Positive tips up. |
| Wing thickness at root [% chord] | 6 | Maximum thickness of the section on the centreline. |
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
| Inlet side wall lean [deg] | 48 | The leading edges of the inlet side walls lean forward from the lower lip up to the fuselage underside by this angle from vertical. |
| Inlet lower lip sweep [deg] | 25 | The lower lip is a chevron: it sweeps back from the centreline to the corners by this angle. |
| Diverter height [in] | 1.8 | Gap between the forebody underside and the splitter plate: the slot that carries the forebody boundary layer past the inlet. |
| Splitter plate thickness [in] | 0.8 | Thickness of the splitter plate (the upper lip of the inlet). It thins to 40 % of this at the leading edge. |
| Splitter plate apex station [% length] | 24.7 | Station of the point of the splitter plate on the centreline, percentage of the fuselage length. |
| Splitter plate sweep [deg] | 36 | Sweep of the splitter plate leading edge, back from the point to the top of the inlet side walls. |
| Diverter wedge sweep [deg] | 50 | Sweep of the wedge that closes the diverter slot behind the inlet lip and turns the boundary layer out to the sides. |
| Inlet lip thickness [in] | 1.34 | Wall between the outer cowl and the duct at the lip. |
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