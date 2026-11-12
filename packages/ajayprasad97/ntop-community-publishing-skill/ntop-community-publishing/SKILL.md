---
name: ntop-community-publishing
description: Prepare and submit nTop notebooks, blocks, scripts, model bundles, and supporting reports to community.ntop.com through the Utilities-community contribution workflow. Use for a new community package, a package update, or a publication audit and PR.
metadata:
  audience: public
---

# Publish to the nTop community

Turn the user's selected work into a portable community package, audit the exact files, and submit the requested contribution. Report whether it is prepared, submitted, merged, or verified live.

The publishing page is [community.ntop.com/#/publish](https://community.ntop.com/#/publish). The contribution repository is [nTopology/Utilities-community](https://github.com/nTopology/Utilities-community).

## Establish the package scope

- Identify the source files, accepted revision, author handle, package slug, and requested destination. Keep source workspaces unchanged and stage publication copies separately.
- Carry forward the user's exclusions, license choice, attribution, and previous authorization. Ask only for unresolved information that changes what can be published. A license approved for one author's examples does not license unrelated material.
- Distinguish a new package from a new revision of an existing package. Check the package directory, prior receipts, and open or merged PRs before choosing a slug or creating a contribution.
- A request to publish includes the required upload and contribution PR. A request only to prepare or audit stops before upload. Do not infer permission to merge, change repository visibility, or bypass the site's review process.

## Read the current contribution contract

Read [the publishing workflow](references/publishing-workflow.md) for repository layout, commands, AI attribution, LFS, and submission states. Verify its dated observations against the current community README, schema, validator, and sync workflow. Prefer the schema over contradictory prose.

Use the publishing page when the user wants the browser flow. For file bundles, an authenticated Git checkout and GitHub CLI can prepare the same contribution directly. Use a fork when direct branch pushes are unavailable. Keep credentials in the configured tools, not in package files.

## Prepare a useful public package

Create `packages/<author>/<slug>/` with:

- `manifest.json`, a clear `README.md`, the approved license text and required credits;
- an explicit primary notebook or other download, its dependencies, and a model-derived cover image;
- requested reports and their local assets, with revision labels and evidence limits;
- a compact record of source hashes, published hashes, changes, and checks.

Use [the manifest example](assets/manifest.example.json) and [the README template](assets/README.template.md) where useful. Replace every illustrative value. The example license, model name, author, and version are not defaults for the user's work.

Give a bundle an explicit `packageFile`. Keep alternate revisions and inspection views distinguishable. Do not rely on alphabetical file order to choose the main model.

State the actual nTop version and any custom build in the README. A schema-compatible version field does not establish compatibility with a public release. Keep recorded native results separate from new native execution and offline packaging checks.

When AI attribution is known, set `aiModel` and add `ai-assisted` to `tags`. Name the model or tool that actually helped build the package (for example `"aiModel": "Claude"`) and keep any README credit consistent with it. Do not infer the model from the agent currently doing the upload.

## Audit the exact upload

Read [the package audit](references/package-audit.md) when notebooks, reports, images, or large files are included. It covers native metadata, dependency closure, embedded images, historical evidence, and downloaded-file checks.

Start with one representative package before scaling a batch. Audit a new revision independently when its files or dependencies differ. Use `uv run` for Python helpers. A schema pass checks the manifest; it is not a native-model or content audit.

Prepare all authorized work before asking for any missing publication approval. Keep the files and remaining decision concrete. Do not add another approval checkpoint when the user already authorized the submission.

## Submit and hand back the result

Follow the command sequence and evidence requirements in [the publishing workflow](references/publishing-workflow.md). Stage only reviewed package files and required attributes. Inspect the diff, validate the staged bytes, push a contribution branch, and open or update the intended PR. Attach it to the current task when the app provides a PR attachment tool.

Record package IDs, commit, licenses, attribution, validation, and PR URLs. The [receipt example](assets/submission-receipt.example.json) shows the state distinctions; replace its illustrative values with observed results. Keep local source paths and private process details out of a public receipt.

If a push or PR creation has an unknown outcome, inspect the remote branch and existing PR before retrying. Stop a dependent submission when a required license, unresolved private content, or unverified file transformation remains. Continue independent preparation and explain the specific missing item.

Report the submitted URL and meaningful checks. Say `live` only after checking the actual community listing and usable download. A successful PR or sync job alone does not establish that state.
