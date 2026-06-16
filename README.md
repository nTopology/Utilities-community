# Utilities-community

A community-maintained collection of nTop notebooks, scripts, and integrations shared by the nTop user community.

## Repository structure

```
packages/
  <author>/
    <package-id>/
      manifest.json
      README.md
      <package-id>.ntop      ← main file (if applicable)
      cover.png              ← cover image shown in the frontend
      ...                    ← any supporting files
```

Each contributor gets their own folder under `packages/` named after their GitHub username or handle. Inside that, each package gets its own folder named after its `id` in `manifest.json`.

## File naming

All files should use **kebab-case slugs** (lowercase, hyphens, no spaces):

```
csv-airfoil-sdf.ntop          ✓
csv-airfoil-support-article.pdf  ✓
CSV Airfoil SDF.ntop          ✗
```

## manifest.json

Every package must include a `manifest.json` at its root. Required fields:

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique kebab-case identifier, matches the folder name | `"csv-airfoil-sdf"` |
| `type` | `"Notebook"`, `"Bundle"`, or `"Installer"` | `"Notebook"` |
| `title` | Human-readable display title | `"CSV Airfoil SDF"` |
| `summary` | One or two sentence description | `"Import airfoil..."` |
| `author` | GitHub username / handle, matches the parent folder | `"jeffh1505"` |
| `version` | Semantic version | `"0.1.0"` |
| `ntopVersion` | Minimum nTop version required | `"4.12+"` |
| `license` | License identifier | `"MIT"` |
| `domain` | Primary domain (e.g. `"Aerospace"`, `"Geometry"`) | `"Aerospace"` |
| `application` | Use case (e.g. `"Analysis"`, `"Geometry"`) | `"Geometry"` |
| `complexity` | `"Beginner"`, `"Intermediate"`, or `"Advanced"` | `"Intermediate"` |
| `tags` | Array of lowercase search keywords | `["airfoil", "csv"]` |
| `preview` | Preview type: `"geometry"` or `"bundle"` | `"geometry"` |

## README.md

Each package should include a `README.md` covering:

- What the package does
- Installation instructions
- Usage steps
- Inputs and outputs table
- License

## Contributing

1. Fork this repo and create a branch.
2. Run the following once to activate the included git hooks:
   ```bash
   git config core.hooksPath .githooks
   ```
3. Add your package under `packages/<your-handle>/<package-id>/`.
4. Make sure `manifest.json` and `README.md` are present and complete.
5. Open a pull request.

### Large files

Files over 50 MB must be tracked with [Git LFS](https://git-lfs.github.com) — the pre-commit hook will catch this and tell you what to run if you forget.
