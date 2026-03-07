# Gotchas

Things that aren't obvious.

## Workspace Members vs Dependencies

Adding a package to `[tool.uv.workspace] members` makes it *available* but doesn't *install* it.

To install, also add to root `dependencies`:

```toml
# pyproject.toml (root)
[project]
dependencies = ["everybase", "eb-pv"]  # <- add here

[tool.uv.workspace]
members = ["src", "ext/eb-pv"]  # <- and here
```

## VS Code / Pylance

When adding new packages, update `.vscode/settings.json`:

```json
"python.analysis.extraPaths": [
  "src",
  "ext/eb-pv/src"
]
```

Then reload VS Code window.

## Package Naming

All extensions use the `eb-*` prefix:

| Context | Style | Example |
|---------|-------|---------|
| Directory | hyphen | `ext/eb-pv/` |
| Import | underscore | `from eb_pv import ...` |
| PyPI name | hyphen | `eb-pv` |
| pyproject.toml name | hyphen | `name = "eb-pv"` |

## isort First-Party

When adding packages, update root `pyproject.toml`:

```toml
[tool.ruff.lint.isort]
known-first-party = ["everybase", "eb_pv", "eb_dict"]  # <- underscore
```

## In-House Dependencies

For in-house libs not on PyPI, use local path in root `pyproject.toml`:

```toml
[tool.uv.sources]
virtuals-py = { path = "../virtuals", editable = true }
```
