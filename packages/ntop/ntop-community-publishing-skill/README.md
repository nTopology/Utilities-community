# nTop Community Publishing Agent Skill

An agent skill that walks an AI coding agent (Claude Code, Codex, or any agent that
reads `SKILL.md` skills) through publishing your work to the nTop community site. Give it
your notebook, block, script, or model bundle and it will:

- stage a publication copy in `packages/<your-handle>/<slug>/` of
  [Utilities-community](https://github.com/nTopology/Utilities-community),
- write the `manifest.json`, README, license, and cover image,
- audit the exact files (native metadata, dependencies, embedded images, large files),
- validate with the repository's manifest validator,
- push a branch and open the contribution pull request,
- report honestly whether the package is prepared, submitted, merged, or live.

It does not merge anything or bypass the site's review process.

The skill's files live in the repository's
[`skills/ntop-community-publishing`](https://github.com/nTopology/Utilities-community/tree/main/skills/ntop-community-publishing)
folder; the download button opens it.

## Installation and use

1. Clone [Utilities-community](https://github.com/nTopology/Utilities-community), or
   download the `skills/ntop-community-publishing` folder from GitHub.
2. Copy that folder into your agent's skills directory, for example
   `~/.claude/skills/` (Claude Code, all projects) or `<project>/.claude/skills/`
   (one project). Other agents: use their skills folder.
3. Install and sign in to the [GitHub CLI](https://cli.github.com/) (`gh auth login`),
   and have `git` and `node` available. Git LFS is only needed for files over 50 MB.
4. Ask your agent, for example: *"Use ntop-community-publishing to publish
   `my-notebook.ntop` to the nTop community as a new package."* Say "prepare and audit
   only" if you do not want it to open a PR.

## Inputs and outputs

| Direction | Name | Meaning |
|---|---|---|
| Input | Your source files | Notebook, block, script, or bundle plus any reports and data |
| Input | Author handle and slug | Your GitHub handle and a kebab-case package name |
| Output | `packages/<handle>/<slug>/` | Manifest, README, license, cover, and files |
| Output | Pull request | A contribution PR against `nTopology/Utilities-community` |

## Evidence and limits

The workflow notes were observed against the Utilities-community repository in
October 2026; the skill tells the agent to re-check the current README and schema before
each submission. The manifest validator checks the manifest only, not native notebook
contents. A merged PR is not the same as a live listing.

## License and credits

MIT, see [LICENSE](LICENSE). Adapted from the community publishing skill in
[nTopology/ntop-api-skills](https://github.com/nTopology/ntop-api-skills). Built with Claude.
