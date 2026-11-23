# Retained source-workspace notes

Paths below describe the original workspace. Use the package README for delivered files.

# Revision O: tail-local ribs and supported spar roots

Open `deliverables/Aircraft-O.ntop` for the main aircraft. The focused tail
models show the revised components without the other aircraft parts.
The HTML report is `../Tail-alignment-review.html`.

Ten separate rib notebooks use the measured local tail frame. The `Aircraft
interior` input is a native implicit body in the aircraft coordinate system.
Each default uses the retained source envelope with its established inset.
Rib-05 moves inboard to intersect both existing spar ends. Geometry records
retain the old identifiers and the new reference Buttline Y positions.

`Rear-tail-cradle-O.ntop` contains both bulkheads, four local fork supports,
the longitudinal webs and eight pin envelopes. Its axial-thickness input has
a nominal value of 1.260 in. The added lands and pocket cutters are fixed to
that nominal configuration. Do not infer a validated range for this control.
The support is an integral geometry study. Its manufacturing segmentation
and structural substantiation are not released.

The main model imports the verified parts as embedded snapshots. Saving a
separate part does not update the aircraft. Rebuild and check the part, refresh
its saved definition in the assembly, then rerun the assembly checks. Scripts
use the qualified native CLI conversion and definition-refresh workflow.

Reproduction order:

1. `tail_alignment.py --plan --ribs` builds the rib geometry.
2. `tail_alignment.py --root` builds the supported tail cradle.
3. `tail_alignment_checks.py --ribs --root` checks native geometry.
4. `tail_alignment_assembly.py` refreshes eleven saved definitions.
5. `tail_alignment_present.py` prepares the native views and deliverables.
6. `tail_alignment_audit.py` verifies the package.
7. `tail_alignment_report.py` writes the report.

Use uv for host Python. Pass a new `--run` value for each native execution;
existing completion receipts cannot be overwritten. The geometry and probes
are reproducible. The presentation script supports camera-specific views.
All report dimensions use inches and Buttline Y. Native geometry remains in
millimeters with SI recipe literals.

The eight failed positions in the retained straight-path trial intersected
intentional pin-head relief. Final checks verify those voids and continuous
solid corridors through the cheek material. No geometry was added to block
head access. Native checks are finite samples, not a global proof of clearance
or strength. No new tail stress, buckling or fatigue analysis is claimed.
