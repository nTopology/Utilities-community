# Contribution workflow

Verified 2 October 2026 against Utilities-community commit `7d26a6ee8d878601ba2f9f3a484c8db5c14c49ea`. Check the current contract before each submission. These are observed repository rules, not a permanent site API.

## Authoritative files

- [README](https://github.com/nTopology/Utilities-community/blob/main/README.md): contribution layout, naming, and hooks.
- [Manifest schema](https://github.com/nTopology/Utilities-community/blob/main/packages/_schema/manifest.schema.json): required keys, values, and limits.
- [Validator](https://github.com/nTopology/Utilities-community/blob/main/scripts/validate-manifests.js): schema plus directory and README checks.
- [Pre-commit hook](https://github.com/nTopology/Utilities-community/blob/main/.githooks/pre-commit): the enforced large-file threshold.
- [Sync workflow](https://github.com/nTopology/Utilities-community/blob/main/.github/workflows/sync-to-private.yml): the observed post-merge route.

The current README still lists `Installer`, while the schema allows `Notebook`, `Block`, `Connector`, `Script`, and `Bundle`. Use the current schema. Unknown manifest properties are rejected.

## Folder and metadata

```text
packages/<author>/<slug>/
  manifest.json
  README.md
  LICENSE
  <slug>.ntop
  cover.png
  reports/                 when reports are requested
  references/              when runtime input files are needed
```

Use lowercase kebab-case names for package files, apart from conventional files such as README.md and LICENSE. `id` must match the slug; `author` must match the parent directory.

Current required fields are `id`, `type`, `title`, `summary`, `author`, `version`, `ntopVersion`, `license`, `domain`, `complexity`, `tags`, and `preview`. `application` is useful but is not schema-required in this snapshot. The current tag limit is eight.

Set `coverImage` and `packageFile` explicitly when the choice matters. Check that they resolve inside the package. For a multi-file bundle, explain how to download the complete directory and keep its dependencies together. Confirm the site's actual download behavior; naming one primary notebook does not ensure that adjacent files are downloaded with it.

Use `aiModel` only for known design/build attribution. A nonempty value should have the `ai-assisted` tag. README wording and manifest attribution should agree. Do not set `featured`, `verified`, or `communitySource` to claim editorial approval. The observed sync preserves private editorial controls and stamps the source marker itself.

## Branch and PR workflow

Use a clean task-owned checkout or a suitable existing worktree. Preserve unrelated local changes. Read repository instructions before running its scripts or hooks.

The following commands illustrate a new package. Replace paths, branch, author, and slug with the actual values. Use the discovered default branch. If using a fork, push there and pass `<fork-owner>:<branch>` as the PR head. A shell script must stop after a failed command; these examples are separate interactive steps.

```powershell
git fetch origin main
git switch -c community/example-package origin/main
git config core.hooksPath .githooks
node scripts/validate-manifests.js
git add -- packages/example-author/example-package
git diff --cached --check
git diff --cached --stat
git diff --cached -- packages/example-author/example-package/manifest.json packages/example-author/example-package/README.md
git commit -m "Add the example community package"
git push -u origin community/example-package
gh pr create --repo nTopology/Utilities-community --base main --head community/example-package --title "Add the example community package" --body-file "publication-pr.md"
```

Write the exact PR prose to the body file before creation. Explain the model, revision, included files, license, and validation limits. Include a concrete primary download and report starting point where appropriate. Use your own GitHub identity. Do not copy an old receipt's identity by accident.

Check for an existing PR before retrying or resubmitting:

```powershell
gh pr list --repo nTopology/Utilities-community --state all --head community/example-package --json number,state,url,headRefOid
gh pr view 123 --repo nTopology/Utilities-community --json url,state,headRefOid,baseRefName,statusCheckRollup
gh pr checks 123 --repo nTopology/Utilities-community
```

PR number 123 is illustrative. Use the returned number. Read validator output and record the commit it applies to. A pending check is not a pass; an empty check list is not a failure. Recheck completion with bounded waits when required for delivery.

## Large files and delivery routes

The current hook requires Git LFS for files larger than `50 * 1024 * 1024` bytes. Measure file sizes. Track the exact files before adding them; do not bypass the hook or use a blanket pattern that affects unrelated files.

```powershell
git lfs install --local
git lfs track "packages/example-author/example-package/example-package.ntop"
git add -- .gitattributes packages/example-author/example-package
git lfs ls-files
```

The observed sync checks out LFS objects in both repositories, then copies changed package directories. Root attributes are not included by that directory copy. Inspect the destination's LFS rules and the deployed download before assuming end-to-end LFS support. Package-scoped attributes can travel with a package, but use them only when compatible with the current deployment. Confirm materialized file size and SHA-256; a 200 response can still return an LFS pointer or HTML error page.

The schema also permits `distribution: "redirect"` with `redirectUrl`. Use that route only for an authorized, durable, accessible artifact. A GitHub page URL is not a direct native-file download. A commit-pinned URL permits a reproducible check; a `main` URL will not expose a new file before merge and can change later. Verify both the intended final route and any temporary review link, and identify that distinction in the receipt.

For bundles, inspect whether the site serves the whole package or just the primary file. Provide a complete, authorized bundle route when needed. Do not create a GitHub release or change storage/public access settings unless that action is within the user's request.

## Submission is not deployment

The observed route is:

1. A contributor submits a PR to **Utilities-community**.
2. After merge, nTop's sync workflow carries the package toward the community site and may open a follow-up review PR in a downstream repository you cannot see or merge.
3. Maintainer review and the normal site deployment make the package available on the community site.

Verify the actual status at each step you report. Do not duplicate any downstream PR or merge anything beyond your own contribution PR just to make the state look complete. A public package deletion also propagates through the current sync, so do not remove an old package as routine staging cleanup.

Use a receipt with `prepared`, `submitted`, `community_merged`, and `live_verified` evidence as needed. Record the observed PR and listing URLs separately. If the task ends at submission, return the PR and do not imply deployment. Monitoring later requires the user's request for follow-up work.
