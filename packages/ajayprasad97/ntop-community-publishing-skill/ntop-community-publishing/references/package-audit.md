# Audit a publication copy

Use checks appropriate to the actual package. A small notebook does not need a solver rerun to be shared. A model bundle with native dependencies and embedded reports needs more than a filename scan.

## Select and preserve the source

- Bind each selected revision to source filenames and SHA-256 hashes. Prefer final delivery receipts over filenames such as `latest` or an arbitrary modification time.
- Distinguish main assemblies, alternate presentations, part notebooks, and unfinished trials. Preserve useful earlier revisions only when they belong in the requested handoff.
- Inspect dependencies before claiming that a notebook is self-contained. Custom blocks can be embedded snapshots while imported airfoils, CAD, tables, textures, and output paths still point elsewhere.
- Keep private source history, task logs, credentials, workstation paths, application binaries, and unrequested generated caches out of the upload. Apply the user's specific holds to package contents, images, and linked downloads.
- Confirm the applicable author license and third-party notices. Public availability is not a license. Preserve derivative-work terms and required corresponding-source links. Do not apply a previous example's license to a new source without support.

## Native notebooks

Inspect native metadata and binary strings as well as the top-level file. Plain `rg` against a `.ntop` file cannot establish that nested, encoded, or compressed data is clean.

If using a native-container reader, first demonstrate a byte-exact parse/serialize round trip on the actual file. Handle variable chunk tables and mixed JSON type case. Use existing qualified tools when available. A tool validated on one build is not proof for every build.

For a publication transformation:

1. Keep the API-saved source and write a separate output.
2. Inventory every machine-specific path. Classify it as an input, an output, or diagnostic text before changing it.
3. For external inputs, include the authorized dependency and adapt the path without changing the data. Explain local reassignment if runtime resolution was not verified. Do not replace all paths with basenames blindly.
4. For outputs, use a portable destination and explain where the user can set a working output directory. Watch for export or command blocks that execute during evaluation.
5. Preserve all function expressions, units, input/output contracts, embedded custom definitions, and binary payloads except explicitly authorized model changes. Retain camera, colors, and visibility for inspection presentations. Collapse authored sections where that matches the requested presentation.
6. Reparse the output and compare the allowed changes with the source. Record source and published hashes and the exact scope of the comparison.

Embedded custom blocks do not automatically update when a standalone part is saved. Say how a consumer refreshes the assembly after a part change. Keep prior-revision analysis attached to that revision.

An offline round trip and graph comparison establish file and graph facts. They do not prove native evaluation, geometric quality, or public-build compatibility. If a native reopen is needed, use an authorized isolated session; do not take over an unrelated user's open notebook. Do not call a modified file natively verified until that check actually completes.

## Reports and images

- Preserve failed screens, assumptions, units, evidence scope, and revision labels. Packaging must not turn an exploratory study into a qualified design claim.
- Keep the HTML and its assets together. Rewrite local model/report links to the delivered filenames. Label omitted material rather than leaving broken links or silently substituting another revision.
- Inspect visible figures and captions, image metadata, inline data URLs, JavaScript image maps, download payloads, and compressed viewer content. Removing a visible photo can leave its encoded copy in the page.
- Check full screenshots for account names, file paths, or unrelated applications. Use an appropriate source render or omit the screenshot when needed. Hash excluded assets and check for copies in every report, even when captions differ.
- Share repeated assets by hash when useful, and remove an excluded asset from every consumer before deleting it. Keep authored plots and native geometry distinguishable.
- Remove remote font/script dependencies when claiming offline support. Preserve the intended appearance with local/system fonts. Use the project's report style rather than inventing a new design requirement for publication.
- Check the downloaded layout at desktop and phone widths, all images, local links, zoom controls, keyboard actions, and any provided theme modes. Exercise lazy-loaded images explicitly during automated checks.

## Final validation and receipt

Run the current community manifest validator, then inspect its coverage. In the recorded version it does not check native contents, file existence for `packageFile`/`coverImage`, model compatibility, or complete bundle downloads. Check those independently.

Audit the exact staged files. Include added LFS attributes, nested assets, and supporting data. Keep symlinks or junctions from importing files outside the selected package without review. Review changes again if files are regenerated after an audit.

When recording published hashes, account for Git line-ending conversion. Either define hashes over the actual committed/downloaded bytes or preserve audited bytes with suitable attributes. Preserve CSV numeric values and Unicode. Do not run broad string replacements through HTML JavaScript or native command literals to remove a path.

Useful receipt fields are source revision/hash, published file/hash/size, allowed changes, native execution status, checks and limitations, license, attribution, commit, PR URL, and live-listing/download status. Record confidential source locations locally, not in public receipts. A compact publication receipt can accompany the package; execution logs and full source workspaces usually should not.

For a batch, maintain a per-package list. One package's clear license or passed audit does not resolve another package's blocker. Submit independently complete packages when authorized and record any held items separately.
