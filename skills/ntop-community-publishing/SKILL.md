---
name: ntop-community-publishing
description: Publish nTop notebooks, blocks, scripts, bundles, or agent skills to community.ntop.com by opening a pull request to nTopology/Utilities-community. Use when the user wants to publish, share, submit, upload, or update something on the nTop community site or in Utilities-community.
metadata:
  audience: public
---

# Publish to the nTop community

Help the user share their work on [community.ntop.com](https://community.ntop.com) by adding it to [nTopology/Utilities-community](https://github.com/nTopology/Utilities-community) through a pull request. The repository is public, so anyone can fork it and contribute. Report honestly whether the work is prepared, submitted (PR open), merged, or live on the site.

The browser alternative is [community.ntop.com/#/publish](https://community.ntop.com/#/publish). Offer it if the user would rather not use git.

## Step 1: Ask what they are publishing

Start by asking what they want to publish, then pick a path. Do not start copying files until the path is clear.

| They have | Path |
|---|---|
| One notebook, block, or script (`.ntop`, `.py`, ...) | **Simple path** |
| A notebook with extra files (input data, CAD, reports, several notebooks) | **Bundle path** |
| An update to something already on the site | **Update path**: find the existing package folder and bump `version`; do not create a second package |
| An agent skill | **Skill path** |

Also ask, if it is not already clear: their GitHub handle (it becomes the folder name) and whether they want to **publish** (open the PR) or only **prepare** (stop before pushing).

## Step 2: Check the work is fine to publish

Everything in the package becomes public. Before copying anything, ask the user to confirm:

- they have the right to publish it (their own work, or they have permission);
- it contains no customer data, confidential or proprietary geometry, credentials, or personal file paths.

If they are unsure about a file, leave it out.

## Step 3: Pick a license

Ask which license applies. Recommend **MIT** for most packages.

> **MIT** is short and permissive: anyone may use, modify, and share your work, including commercially, as long as they keep your copyright notice. You give no warranty. It is the simplest choice and the usual one for community examples.

If they want something else, help them choose briefly: **Apache-2.0** is similar to MIT with an explicit patent grant; **CC-BY-4.0** suits documents and data rather than code; a copyleft license such as **GPL-3.0** requires derivative work to stay open. If their work builds on someone else's, respect that work's license and keep the required credits. Put the license text in a `LICENSE` file and the identifier in the manifest.

## Step 4: Set up GitHub access

Contributions go through a fork, so no special permission is needed. Check the tools first:

```bash
gh --version          # GitHub CLI; install from https://cli.github.com if missing
git --version
gh auth status        # must show a logged-in github.com account
```

If `gh auth status` fails or a later `gh`/`git` command reports an auth error, walk the user through it: run `gh auth login`, choose GitHub.com, HTTPS, and the browser login. The default scopes are enough to fork and open a PR. Then run `gh auth setup-git` so `git push` uses the same login. If they cannot use the CLI, point them to the browser flow above.

Fork, clone, and branch (use their own handle and slug):

```bash
gh repo fork nTopology/Utilities-community --clone
cd Utilities-community
git switch -c add-<slug>
```

If they already have a fork, update it first (`gh repo sync <their-handle>/Utilities-community`) and branch from the latest `main`. Keep unrelated changes out of the branch.

## Step 5: Build the package

Read the current contract before writing a manifest: the repository `README.md` and `packages/_schema/manifest.schema.json` (the schema wins over prose). See also [the contribution reference](references/publishing-workflow.md).

Create `packages/<handle>/<slug>/` with:

- the file(s) to publish, named in lowercase kebab-case (`my-block.ntop`, not `My Block.ntop`);
- `manifest.json`: `id` equals the slug and `author` equals the handle;
- `README.md`: what it does, install and use steps, inputs and outputs, license; [a template](assets/README.template.md) helps;
- `LICENSE`;
- `cover.png`: a screenshot or render of the actual model. Ask the user for one if they have it.

Manifest rules to follow exactly (see [the example](assets/manifest.example.json); replace every illustrative value):

- `domain` must be one of the values listed in the schema's `domain` enum. Read the enum from the schema and offer only those; if none fits, ask the user to choose the closest. Never invent a domain.
- `version` is `MAJOR.MINOR` (for example `1.0`); three parts also validate.
- `ntopVersion` is the nTop version the user actually used, as `MAJOR.MINOR` (for example `6.2`) or with a trailing `+` for "this version or newer" (`6.2+`).
- `type`, `complexity`, `preview`, tag count, and other fields follow the schema. Unknown fields are rejected.
- Set `packageFile` to the main download when the package has several files.
- Do not set `featured`, `verified`, or `communitySource`; those are editorial.
- If an AI model helped build the package, set `aiModel` to its name and add the `ai-assisted` tag. Ask; do not guess.

Simple path: this is all that is needed. Copy the file, write the manifest and README, add the license.

Bundle path: also keep dependencies together in the folder, make sure the README says which file to open first and what else must sit beside it, and read [the package audit](references/package-audit.md) for notebooks that reference external files, reports, and images. Check for machine-specific paths and embedded private content.

Skill path: put the skill in `skills/<skill-name>/SKILL.md` (with any `references/` or `assets/`), add a row to `skills/README.md`, and add a listing package at `packages/<handle>/<skill-name>-skill/` with `"type": "Agent Skill"`, `"distribution": "redirect"` and a `redirectUrl` pointing at the skill's folder, so there is one copy and no zip.

If `node` is available, `node scripts/validate-manifests.js` is a quick check of the manifest. If it is not, CI runs it on the PR.

### Large files

Git rejects files over 50 MB unless they use Git LFS, and the repo's pre-commit hook enforces this. For such a file, track exactly that file before adding it:

```bash
git lfs install --local
git lfs track "packages/<handle>/<slug>/<large-file>"
git add .gitattributes
```

Do not use a broad pattern or bypass the hook.

## Step 6: Review, then submit

Show the user a short summary before pushing: the files being added, the license, and the PR title. Skip the extra question only when they clearly asked you to publish and nothing is ambiguous.

```bash
git config core.hooksPath .githooks
git add -- packages/<handle>/<slug>        # plus .gitattributes and skills/ changes if used
git diff --cached --stat
git commit -m "Add <title>"
git push -u origin add-<slug>
gh pr create --repo nTopology/Utilities-community --base main --title "Add <title>" --body "<what it is, nTop version, license>"
```

Check for an existing PR for the same package before creating another. If a push or PR command fails with an unclear result, inspect the branch and `gh pr list --repo nTopology/Utilities-community --head <branch>` before retrying.

Do not merge anything, change repository settings, or try to bypass review. A maintainer reviews and merges the PR.

## Step 7: Hand back the result

Give the user the PR URL and what is included. Explain what happens next: after a maintainer merges the PR, the package goes through the site's normal sync and review, so it will not appear on community.ntop.com immediately. Say `live` only after checking the community listing and that the download or link works. An open or merged PR alone does not mean the package is live.
