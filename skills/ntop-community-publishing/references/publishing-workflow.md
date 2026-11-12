# Contribution reference

Rules observed in Utilities-community in October 2026. The repository is the source of truth, so check these files before each submission and prefer them over this page. The commands for forking, branching, committing, and opening the PR are in [SKILL.md](../SKILL.md).

## Authoritative files

- [README](https://github.com/nTopology/Utilities-community/blob/main/README.md): contribution layout, naming, and hooks.
- [Manifest schema](https://github.com/nTopology/Utilities-community/blob/main/packages/_schema/manifest.schema.json): required keys, allowed values (including `domain`), and limits.
- [Validator](https://github.com/nTopology/Utilities-community/blob/main/scripts/validate-manifests.js): schema plus directory and README checks. CI runs it on every PR.
- [Pre-commit hook](https://github.com/nTopology/Utilities-community/blob/main/.githooks/pre-commit): enforces the large-file threshold.

The README may still list `Installer` as a type. Use the schema's list. Unknown manifest properties are rejected.

## Folder layout

```text
packages/<author>/<slug>/
  manifest.json
  README.md
  LICENSE
  <slug>.ntop              the main download
  cover.png
  reports/                 optional
  references/              optional runtime input files
```

Use lowercase kebab-case names, apart from `README.md` and `LICENSE`. `id` must equal the slug, and `author` must equal the parent folder.

Required manifest fields: `id`, `type`, `title`, `summary`, `author`, `version`, `ntopVersion`, `license`, `domain`, `complexity`, `tags`, `preview`. `application` is useful but optional. At most eight tags.

`coverImage` and `packageFile` name files inside the package folder. Set `packageFile` when a package has several files, since the site otherwise guesses the main download. The site's download button may serve only that primary file, so tell users in the README which other files must sit beside it.

`aiModel` records known AI help and goes with the `ai-assisted` tag. `featured`, `verified`, and `communitySource` are editorial; contributors do not set them.

## Checking a PR

After opening a PR, check it and any existing PR for the same package:

```bash
gh pr list --repo nTopology/Utilities-community --state all --head <branch> --json number,state,url
gh pr checks <number> --repo nTopology/Utilities-community
```

A pending check is not a pass, and an empty check list is not a failure. If CI reports a manifest error, fix it on the same branch and push again; the PR updates itself.

## Large files

The pre-commit hook requires Git LFS for files over 50 MB. Track the exact file, not a broad pattern, before adding it (commands are in SKILL.md). Check the deployed download afterwards: a successful response can still return an LFS pointer instead of the real file.

## Redirect packages

`"distribution": "redirect"` with `redirectUrl` sends the site's button to an external URL instead of a file in the package folder. Use it when the content lives elsewhere in the repository (an agent skill) or at a durable public URL. A link to a GitHub page is not a direct file download. A link to `main` only works after the PR merges.

## Submission is not deployment

1. The contributor opens a PR to **Utilities-community**.
2. A maintainer reviews and merges it.
3. nTop's sync and site deployment then publish it, which takes additional time and review the contributor cannot see or do.

Stop at the PR you opened. Do not merge anything, duplicate follow-up PRs, or delete an existing public package as cleanup; deletions propagate to the site.
