# Retained source-workspace notes

Paths below describe the original workspace. Use the package README for delivered files.

# Revision N native aircraft models

Open `deliverables/Aircraft-N.ntop` for the current structural assembly.
The installed and exploded viewing models add zero-thickness skin layout surfaces.
Keep `exports/panels-connected/` with this project. The mesh imports currently use
absolute paths. Relink them when moving the project to another computer.

## Tail support

Two transverse bulkheads sit at the measured front and rear tail-spar roots.
Their stations are 305.463 and 326.767 inches. Longitudinal root webs connect them.
The complete tail support is an embedded custom block in the main assembly.
It includes the forks, pin envelopes, spar sockets and head-access reliefs.
The four retained tail spars have matching bores.

`Tail-front-bulkhead-N.ntop` and `Tail-rear-bulkhead-N.ntop` expose the separate
bulkhead construction. They share the support's pocket, passage and relief
definitions. They do not define a manufacturing split in the integral cradle.
Use `Rear-tail-cradle-N.ntop` to inspect the complete support and hardware.
The axial-depth input is nominally 1.260 inches. Pocket cutters retain fixed
positions for this revision. Changing that input requires new web-gauge checks.

The main assembly stores imported definitions as snapshots. Saving a separate
notebook does not automatically update the main model. The current rebuild path
uses shared source geometry, native extended recipes, and explicit saved-definition
refresh. It does not claim a live Notebook API session.

## Rebuild

Run scripts from the Airplanes repository with its existing uv environment.
Use a new run identifier for each command. Completion receipts are retained in
`execution/`. Do not repeat a command whose outcome is unknown.

1. `spaced_structure.py --plan` computes tributary loads and the rib sizing screen.
2. `spaced_structure.py --ribs --run <new-id>` creates the retained native ribs.
3. `spaced_structure.py --tail --run <new-id>` creates the complete tail support
   and drilled tail spars. The measured source sections are retained in geometry.
4. `spaced_tail_parts.py --run <new-id>` exposes the two separate bulkheads.
5. `spaced_skin.py` partitions the retained aircraft source surface.
6. `spaced_present.py --skins --run <new-id>` builds native skin views and drawings.
7. `spaced_checks.py --ribs --tail --run <new-id>` evaluates native geometry probes.
8. `spaced_assembly.py --run <new-id>` refreshes native definitions and verifies
   the complete assembly output through native extended readback.
9. `spaced_present.py --assembly --run <new-id>` creates the full viewing models.
   Use `--tail` and `--tail-context` for the support and attachment detail views.
10. Render each view with `spaced_present.py --render <name> --run <new-id>`.
11. `spaced_audit.py` checks the final composition, part hashes and panel labels.
12. `spaced_report.py` writes `Spaced-structure-review.html` in the project root.

The `parts/` folder contains canonical computational notebooks. The `deliverables/`
folder contains organized viewing notebooks. Each main-model refresh must precede
rebuilding the assembly views. Native readback verifies definition identity and
expression equality. View audits compare native blocks, literals and imported
definitions. Unversioned custom-function calls resolve to the unique recorded
native definition of the same name and input signature.

## Analysis limits

The rib study retains the preceding pressure distribution and load factors.
It increases retained rib gauges for larger tributary loads. The mass comparison
covers ordinary ribs only. Root closures and any later skin reinforcement are
excluded. The tail bulkheads use proposed dimensions, without tail-load sizing.
Native field samples establish selected geometry features, not global strength.

Skin and stringer buckling, tail loads, pin bearing, fatigue, frame attachments,
production segmentation, tolerances and catalog hardware remain open. The model
is a design study. It is not a manufacturing or flight release.

Revisions L and M, their reports, and their original detailed skin images remain.
