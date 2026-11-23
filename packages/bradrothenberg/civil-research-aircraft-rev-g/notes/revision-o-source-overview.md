# Retained source-workspace notes

Paths below describe the original workspace. Use the package README for delivered files.

# Revision O full-aircraft presentation

The main review is `../Design-review.html`. It combines the canonical O
structure with the retained N set of 77 exterior panel surfaces.
The previous main review is preserved at `../Design-review-F.html`.

`parts/Aircraft-O.ntop` remains the canonical source. The viewing notebooks
preserve its structural output, literal inputs and embedded definition chunks.
The panel display graph imports the verified N meshes. Keep
`../spaced_structure/exports/panels-connected/` when moving the viewing models.
The stored mesh references use the original absolute paths.

The panel surfaces have no physical sheet gauge. The close-up panel, carrier
and fastener images are retained from Revision L. Its historical W01 sample is
smaller than the merged current wing-root skin and does not detail that entire
new panel's attachments.

## Reproduction

Use uv from the repository root. Build 42926 is selected in `config/runtime.json`.
The following scripts live in `CivilResearchAircraft/scripts/`:

- `aircraft_overview_o.py`: compose native structure and panel views; compare
  their native graphs, literal values, mesh hashes and embedded definitions.
- `aircraft_overview_quality.py`: prepare shorter contiguous display regions
  and higher implicit sampling. The regions are display boundaries, not cuts.
- `aircraft_main_report.py`: compose the report, retained drawings, detailed
  fastener images and the source-linked revision evolution chart.
- `aircraft_main_report_audit.py`: check native provenance, completed renders,
  report assets, labels, panel schedule and live HTTP download links.

Use unique render run IDs. Keep every completion or timeout receipt. Do not
run GPU-heavy scene renders in parallel. Earlier concurrent high-resolution
trials exhausted the shared GPU resources.

## Evidence

`evidence/revision-history.json` records development stages and their sources.
Candidate C and the edge-alignment study are development studies, not extra
lettered releases. No separately delivered Revision C is recorded.

`evidence/main-report-content.json` records figure hashes.
`evidence/main-report-package.json` records completed rendering and HTTP checks.
Earlier O geometry evidence remains separate. This report update runs no new
structural solve and grants no additional strength or manufacturing status.

## Completed overview renders

All three views use 3840 x 2400 pixels, High implicit sampling (CLI level 3),
ambient occlusion off and 96 contiguous longeron display regions. These
regions shorten the display bounds without cutting the structural parts.

| View | Render time, s | Completion receipt |
| --- | ---: | --- |
| Full exposed structure | 774.98 | `execution/Full-structure-O-quality-quality01.json` |
| Installed skins | 771.47 | `execution/Aircraft-skin-installed-O-quality-quality01.json` |
| Exploded skins | 644.27 | `execution/Aircraft-skin-exploded-O-quality-quality01.json` |

The longerons render continuously in these views. Some long spar faces retain
fine display banding. The report supports full-resolution image enlargement.
`evidence/main-report-browser.json` records the final browser verification.
