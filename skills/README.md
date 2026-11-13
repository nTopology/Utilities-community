# Agent skills for nTop

Skills that AI coding agents (Claude Code, Codex, and others that read `SKILL.md`) can use
when working with nTop and the nTop community. Copy a skill folder into your agent's skills
directory (for example `~/.claude/skills/`).

| Skill | Use it to |
|---|---|
| [ntop-community-publishing](ntop-community-publishing) | Package, audit, and submit notebooks, blocks, scripts, and bundles to the community site through a pull request |

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md` with `name` and `description` frontmatter, plus
   any `references/`, `assets/`, or `scripts/` it needs.
2. Add a row to the table above.
3. Add a listing package under `packages/<author>/<skill-name>-skill/` with
   `"type": "Agent Skill"`, `"distribution": "redirect"` and a `redirectUrl` pointing at the skill's folder, so the
   skill has one source of truth and no zip to keep in sync.
