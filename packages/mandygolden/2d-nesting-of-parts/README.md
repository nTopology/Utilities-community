# 2D Nesting of Parts — nesting implicit bodies on the build plate from inside nTop

> Download this whole folder (not just one file) — `nest_pack.exe`, the demo
> notebook and the notices below all travel together.

This package contains everything needed to use the `2D Nesting of Parts` custom block: the block,
a demo notebook, the packer executable it calls, and a short deck that explains how it works.

## What you need

1. **nTop 6.3.3 or newer.** The block is embedded in `2D Nesting on Build Plane Example.ntop` and
   saved on its own as `2D Nesting of Parts.ntop`; nothing has to be registered.
2. **A writable Work Folder that holds `nest_pack.exe`.** The exe is self-contained (its own Python,
   numpy and Pillow): nothing is downloaded, nothing is installed. Windows only. See
   "Third-party components" below for what it contains.
3. **One permission per Work Folder.** The first time nTop sees the command text it asks whether
   the notebook may run an external command; allow it once. Parameters travel in `params.csv`, so
   the text only changes when the Work Folder changes.

## Contents

| Item | What it is |
|---|---|
| `2D Nesting of Parts.ntop` | the custom block: five inputs, one output, seven commented sections |
| `2D Nesting on Build Plane Example.ntop` | the demo notebook, with the block wired to nine test bodies and an EOS M 280 plate |
| `nest_pack.exe` | the packer, a self-contained Windows executable; copy it into any Work Folder |
| `nest_pack.py` | the packer's source, for reading and editing; `scripts/build_exe.ps1` rebuilds the exe from it |
| `THIRD-PARTY-NOTICES.txt` | the full licence texts of everything frozen into the exe; keep it next to `nest_pack.exe` |
| `2D Nesting of Parts.pdf` | the deck: what the block does, how it works, how to use it, limits |
| `scripts/build_exe.ps1` | rebuilds `nest_pack.exe` from `nest_pack.py` (needs `uv` and internet once) and regenerates the notices with `scripts/make_notices.py` |

## Getting started

1. Download this folder to somewhere you can write to. That folder is a ready-made Work Folder
   because it already holds `nest_pack.exe`.
2. Open `2D Nesting on Build Plane Example.ntop` and set the **Work Folder** variable to that
   folder's path. Build; allow the external command when nTop asks. The nine bodies rotate and move
   onto the plate.
3. In your own notebook, either embed `2D Nesting of Parts.ntop` (Custom Blocks panel → import) or
   copy the `Nested Parts` block out of the demo. Wire your bodies as one implicit list, the build
   plane and build volume box (for example from the EOS M 280 toolkit block), a Part Spacing, and a
   Work Folder that contains `nest_pack.exe`.

## The block

Inputs: `Bodies` (list of implicit), `Part Spacing` (mm, 0 = shadows touch), `Build Plane`
(plate plane, normal up, parallel to world XY), `Build Plate` (the build volume box), `Work Folder`
(text). Output: the bodies rotated about Z and moved onto the plate. Parts that fit nowhere are
parked in a row beside the plate's +X edge and listed in `unplaced.csv`.

| Section | Named blocks | What happens |
|---|---|---|
| Settings | Part Lift 5 mm, Rotation Step 15°, Plate Margin 0, Raster Pixels 400, Shadow Clearance 10 mm, Shadow Feature Size 0.5 mm, Packer Timeout 900 s | tunables |
| Shadows | Lowest Body Z, Build Plane Z, Shadow Plane, Section Plane, Shadows | shadow plane 10 mm below the lowest body (never above the plate); support volume at 90° overhang → vertical prism → implicit |
| Bounds | X/Y/Z Field, Shadow Min/Max X/Y, Section Z, Shadow Boxes | extents through plane-distance fields; image boxes |
| Export to Work Folder | Shadow Image Paths, Shadow Images, Parts Columns, Parts File, Packer Params, Params File | one image per shadow, parts.csv, params.csv |
| Run the packer | Packer Command, Export Files, Exports Done, Packer Run | `"<Work Folder>/nest_pack.exe" "<Work Folder>"`; timeout tied to the exports |
| Import placements | Exit Code, Result File, Placements, Angles, Moves | `placements<exit code>.csv` → degrees and millimetres |
| Apply placements | Nested Bodies | rotate about Z through the origin, then translate |

## The packer

`nest_pack.py`, about 280 lines of numpy and Pillow, built into `nest_pack.exe` with PyInstaller.
It reads `parts.csv`, `params.csv` and the `shadow_<i>` image archives, resamples each shadow onto
a 0.5 mm grid (coarser when the largest part passes about 110 mm), and does bottom-left fill on a
boolean occupancy grid: a FFT correlation finds every free position in one pass, placed parts are
dilated by the spacing, the smallest nest bounding box wins. Up to four bodies every order is
tried; more get four to six orders under a 240 s budget. Parts that fit nowhere are parked in a
row beside the plate (placed = 0 in `placements0.csv`, indices in `unplaced.csv`) so the nest
still builds and the leftovers can go on a second plate. `nest_pack.log` records everything.

Tested on thirteen geometry cases (single and many bodies, rods, rings, plates with holes, thin
sheets, bodies far from the origin or below the plane, spacing, oversized and too many parts), all
passing.

## Third-party components

The packing algorithm (`nest_pack.py`) is nTop's own code; no third-party nesting library is used.
`nest_pack.exe` is that script frozen together with the open-source components below, each under
its own licence (all permissive for redistribution):

| Component | Version | Licence | Used for |
|---|---|---|---|
| Python | 3.12 | PSF License 2.0, https://docs.python.org/3/license.html | the interpreter inside the exe |
| numpy | 2.5 | BSD 3-Clause, https://numpy.org/doc/stable/license.html | raster masks and the FFT correlation |
| Pillow | 13.0 | HPND (MIT-CMU), https://pillow.readthedocs.io/en/stable/about.html#license | reading the shadow images |
| PyInstaller bootloader | 6.22 | GPL 2.0 with the Bootloader Exception, https://pyinstaller.org/en/stable/license.html | starting the frozen program |

The PyInstaller exception allows programs built with it to be distributed under any terms. `uv`
is used only to build the exe and is not shipped. The full licence texts, including those of the
libraries numpy bundles, are in `THIRD-PARTY-NOTICES.txt`.

## Limits and notes

- Only the XY footprint is checked; a part taller than the build volume is not rejected.
- `nest_pack.py` dilates each raster by one cell for safety; remove that for closer contact.
- Rotation is about Z only, in steps of `Rotation Step`; bodies are not re-oriented in 3D.
- If the Run Command block sits unbuilt after a recipe import, toggle one of its inputs.
- The demo notebook still lists older block definitions from earlier embeds in its Custom Blocks
  panel; they can be removed there.

## License

This package (the custom block, demo notebook, packer source, deck and scripts) is released
under the MIT License — see `LICENSE`. The third-party components frozen into `nest_pack.exe`
keep their own licenses, listed above and in full in `THIRD-PARTY-NOTICES.txt`.

Built with AI assistance (Claude).
