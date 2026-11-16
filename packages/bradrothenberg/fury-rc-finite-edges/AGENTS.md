# Instructions for an agent branching this package

Read this before changing anything if you are an AI coding agent (or a person working like one) asked to make a variant
of this model: another tail, another inlet, a different aircraft on the same method. People who only want to use the
notebook should read [README.md](README.md) and [docs/guide.md](docs/guide.md) instead.

## 1. The notebook is generated: change the Python, not the notebook

- `fury-rc-finite-edges.ntop` is written by `ntopcl convert` from a recipe that the Python in `model/` produces. Do not
  edit the `.ntop` file by hand or with a script: the next build overwrites it, and a broken edit can make it unopenable.
- Changing an **input value** needs no build: open the notebook in nTop and change it in sections 01 to 06.
- Changing a **shape, a part or an input's meaning** is done in `model/`, then the notebook is rebuilt (section 4).
- Everything you add must end up as fields in the recipe. Meshes, images and files on disk do not travel with the notebook.

## 2. Map

| Path | What it is |
|---|---|
| `model/design.py` | Every input: key, label with unit, default, notebook section, one-sentence description. `Design(key=value)` overrides a default |
| `model/oml.py` | The outside: guide curves, section control nets, fuselage lofts, inlet, diverter, duct, wing, tail (`Airframe`) |
| `model/aircraft.py` | The bodies: skin, frames, spars, ribs, engine, jet pipe, fuel, mission bay; `build()` returns every body with its colour, section and box |
| `model/gear.py`, `model/fittings.py`, `model/livery.py` | Landing gear and bays; pylons, rails, fairings, antennas; panel lines, paint, markings |
| `model/fieldlab.py`, `shapes.py`, `regions.py`, `registry.py`, `preview.py` | The field library (graph, evaluation, meshing, recipe writer), shape helpers, mesh cache, cameras and renderer |
| `tools/` | Quick looks, renders, sections, notebook build, nTop mesh check (section 4) |
| `analysis/` | Weights, duct areas, vortex lattice; results in `analysis/results/` |
| `flight/` | Flight study: the aircraft as numbers (`aircraft.py`), turn performance against an F-16C reference (`turn.py`), the 6-DOF block graph and its flights (`sim/`), charts and approach pictures. Start at `flight/README.md` |
| `native/notebook/` | The recipe (`fury.json`), which section each variable belongs to (`fury_layout.json`), check values (`fury_checks.json`), counts (`fury_presentation.json`) |
| `docs/` | Guide, input table, photograph match, proportions and where each came from, analysis notes, photograph sources |
| `publication-checks.json` | Notebook hash and the nTop mesh comparison of the published build |

## 3. Set-up

- Python 3.12 with numpy, torch, scipy, matplotlib, pyvista (with vtk) and pillow. Published with numpy 2.5, torch 2.6
  (CUDA), scipy 1.18, pyvista 0.49.
- `FIELDLAB_DEVICE=auto` uses the GPU when there is one, `FIELDLAB_DEVICE=cpu` forces the processor. The renderer at
  full resolution took about 40 GB of GPU memory on the author's workstation; use a larger `scale` (coarser) if you have less.
- Rebuilding the notebook needs nTop 6.3 on Windows. The path to `ntopcl.exe` is a constant near the top of
  `tools/build_native.py` and `tools/pilot.py`; change it there if yours is elsewhere. Run only one `ntopcl` job at a time.
- Run every command from the package folder. Tools write scratch files to `.local/` and pictures to `preview/`; neither
  belongs in a published package.

## 4. The loop

Times are from the author's workstation (one 48 GB GPU) and are only a guide. `key=value` arguments override inputs,
for example `tail_type=1 gear_down=0 wing_stores=0`.

| Step | Command | Time | What to look at |
|---|---|---|---|
| Does it still build? | `python tools/build_native.py --stem trial --no-convert` | 10 s | Body, variable and node counts, and the eight check values. The slot value must be positive (air) and the plate value negative (solid) |
| Outside, coarse | `python tools/quick.py <tag> 14 [key=value] [shots]` | 15 s | `preview/<tag>/*.png`; shot names are in `model/preview.py` |
| Fuselage cuts | `python tools/sections.py <out.png> [stations as fractions]` | 10 s | Wall thicknesses, the splitter plate, duct against structure and fuel |
| Every body | `python tools/render_parts.py <tag> [scale] [key=value] [--exterior] [--cut] [--zone x0 x1 skin_scale] --shots a b c` | 1.5 min at scale 1.6, far longer at 0.8 | `--shots` goes last. `--cut` opens the port side. `--zone` meshes part of the skin finer for close-ups |
| Duct | `python analysis/duct.py` | 1 min | Capture, throat and engine face areas; line of sight. `tools/tune_duct.py` proposes floor heights for a chosen area ratio |
| Weights | `python analysis/mass.py` | 10 min the first time | Weights and centre of gravity. Estimates: the assumptions are printed |
| Stability | `python analysis/vlm.py` | 5 s | Lattice neutral point against the centre of gravity. Run after `mass.py` |
| Notebook | `python tools/build_native.py` | about 10 min | Writes `native/notebook/fury.ntop`; copy it over `fury-rc-finite-edges.ntop`. Then read `native/notebook/fury_presentation.json`: `computation_unchanged` must be true and `variables_used_before_they_are_defined` empty |
| nTop against Python | `python tools/pilot.py exterior 12` and again with `tail_type=1` | about 25 min each | `native/pilot/*_verify.json`: nTop meshes the outside, Python evaluates the field at every vertex. Published build: 99 % of vertices within 0.002 in, largest difference 0.12 in |

Look at pictures and sections after every geometry change, before the long steps. A change that looks right from outside
can be wrong inside.

## 5. Where to change what

| To change | Edit |
|---|---|
| A default, a label, a description, a new input | `INPUTS` in `model/design.py` (pick the section constant `S_FUS` ... `S_GEAR`); read it with `d.m()`, `d.raw()`, `d.tan()` and so on |
| Fuselage profile, breadth, chine, belly, duct roof and floor | The guide curves at the top of `model/oml.py` (`_g(name, stations, values)`): stations are fractions of the length, values fractions of the reference length |
| Fuselage section shape | The control nets in `model/oml.py` (`TRAPEZOID_NET`, `ROUND_NET`, `KEEL_NET`) and the guide that blends them along the length |
| Inlet face, lips, splitter plate, diverter slot | `lip_plane`, `inlet_face`, `plate_top`, `diverter_slot`, `duct_core`, `lower` in `Airframe` |
| Wing or tail planform and thickness | Inputs only. All four surfaces come from one routine |
| A new body | A method in `model/aircraft.py` (or `gear.py`, `fittings.py`) that returns a field, added in `build()` with a material from `registry.MAT`, a section and a box |
| Panel lines, paint, markings | `model/livery.py`: flat patterns intersected with a thin layer on the outside |
| A new camera | `SHOTS` in `model/preview.py` |

## 6. Conventions in the code

- **Units:** inputs and everything shown to a person are in ft, in, deg, lb, US gal. The model computes in metres. X aft
  from the nose, Y to starboard, Z up.
- **Reference size:** the lofts are defined at a reference length (`LREF` in `model/oml.py`) and scaled by the length and
  breadth inputs. Inside the loft code use the reference coordinates `af.xr`, `af.yr`, `af.zr`, not X, Y, Z.
- **Names are the notebook:** `field.named('Label', SECTION)` makes a variable with that name in that section. Anything
  not named becomes an automatic step called `Parent | Clamp 37`. The landing gear, markings and fittings are full of
  those and are hard to read; when you add a part, name the steps a reader should follow and keep each part to a few of them.
- **Switches** are inputs of 0 or 1 that move a part far away or bring it back (`tail_type`, `gear_down`,
  `wing_stores`): follow the existing pattern so the switch still works inside nTop.
- **One definition per field:** methods of `Airframe` cache their result (`self._once`). Reuse them instead of building
  the same field twice, or the notebook gets duplicate variables.
- **No reads from disk in the model:** a number taken from a photograph or a fit is written into the source with a comment
  saying where it came from.

## 7. Traps that cost time on this model

- **Thin walls vanish under a smooth union or intersection applied after hollowing.** A 1 in splitter plate disappeared
  when a 2 in rounding was applied after the duct was cut out. Round first, hollow second, and check with
  `tools/sections.py` and the two check values (slot, plate).
- **Check points must follow the model.** Hard-coded coordinates stopped testing what they were named for after the shape
  moved. The slot and plate points are found by scanning the model; do the same for new ones.
- **Handing one surface over to another along the length** (the plate to the duct roof) can open a leak where the first
  is still needed. Cut sections through the whole hand-over.
- **The duct shares the fuselage with the wing carry-through, the fuel and the gear bays.** After moving any of them,
  cut sections and rerun `analysis/duct.py`: a filled duct is invisible from outside.
- **Dark photographs hide shape.** Brighten and crop before reading an edge from one. One photograph gives one view:
  say so when a dimension rests on a single picture.
- **A build that converts is not a build that is right.** `ntopcl` can also return a non-zero exit code after writing a
  complete result; judge by the output file and the comparison, and say what you saw.

## 8. What this package cannot reproduce

- **Photograph match** (`tools/match.py`, `docs/match.md`) and the generated documents (`tools/write_docs.py`) need the
  reference photographs, which are third-party and not included. `docs/sources.md` lists the page of each. Without
  them, update the numbers in the documents by hand and say the match was not rerun.
- **The flow solution** in `docs/analysis.md` used a solver that is not public. Do not carry its numbers over to a
  changed shape. If you run a flow solver of your own on a mesh from `registry.surface_mesh`, pass the faces through
  `registry.orient_faces` first: the mesher leaves some triangles along sharp edges turned the wrong way. The mesh is
  still closed, so a closedness check passes, but a solver that takes inside and outside from the normals will mark
  air behind the trailing edges as solid. The first published flow numbers were wrong for that reason.
- **The 6-DOF flights** (`flight/sim/maneuvers.py`, `flight/sim/fly.py`) need the Unlinked command-line program built
  with the small patch in `flight/sim/` (`flight/README.md`, "The engine"). Without it `flight/aircraft.py`,
  `flight/turn.py`, `flight/sim/model/build_model.py`, `flight/sim/params.py` and `flight/charts.py` still run. After a
  change of shape or weight: rerun `analysis/mass.py` and `analysis/vlm.py`, delete `flight/out/lattice.json` (a cache)
  and `analysis/results/flow_points.json` (flow-solution points of the published shape; without the file the flight
  model takes lift and moment at zero angle of attack as zero), then run `flight/aircraft.py` and `flight/turn.py`.
  If you cannot run the engine, say that the flights in `flight/README.md` are those of the published shape. Every
  number in `flight/` is an estimate; keep the labels.
- **The published pictures** in `docs/img/` were made with `tools/render_parts.py` and assembled by a script that is not
  included. Rerender the ones your change affects.

## 9. Before you say it is done

1. Pictures of the changed area from at least three sides, and sections through it, looked at by you.
2. `build_native.py --no-convert` runs; the slot and plate checks have the right signs.
3. Both switch positions of every switch you touched still build (`tail_type`, `gear_down`, `wing_stores`).
4. Analysis rerun where the change can matter (duct after inlet or fuselage changes, mass and stability after anything heavy).
5. Notebook rebuilt and copied to the package root; `computation_unchanged` true; nothing used before it is defined.
6. nTop mesh check run on the final shape for each tail, or a plain statement that it was not.
7. `README.md`, `docs/guide.md`, `docs/inputs.md`, `docs/proportions.md` and `publication-checks.json` agree with the
   model: counts of inputs, variables and bodies, areas, weights, limits.
8. No file paths from your machine, no private data, no third-party photographs in the package.

## 10. Reporting

- Say which results are measured, which are estimates and which were not rerun. Keep the limits in `README.md` true for
  your variant: no dimensions of the aircraft are published, the size comes from one photograph, the inside is
  representative, the stability of the model as built is not shown.
- This is an independent model from public photographs. Do not add manufacturer data, do not reproduce the
  manufacturer's logo, and do not present a variant as the real aircraft.

## 11. Publishing a branch to the community site

- A variant is a new package: `packages/<your handle>/<new slug>/` with its own `manifest.json` (`id` equal to the slug,
  `author` equal to the handle), cover picture and README. Do not overwrite this package unless you are updating it for
  its author; an update keeps the folder and raises `version`.
- The licence is MIT: keep `LICENSE` and its copyright notice, and say in your README that the work is derived from
  this package.
- File names in lowercase kebab-case; set `aiModel` only to a model that was really used.
- Follow the repository's own publishing instructions (`skills/ntop-community-publishing/`), run its manifest validator,
  and open a pull request. Report whether the work is prepared, submitted or merged; do not call it published before it is merged.
