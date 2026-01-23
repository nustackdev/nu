# Gotchas

Things that aren't obvious.

## Git Dependencies

For packages not on PyPI (like `pv`), use git source in package's `pyproject.toml`:

```toml
[project]
dependencies = ["pv"]

[tool.uv.sources]
pv = { git = "https://github.com/everyabc/pv" }
```

## Workspace Members vs Dependencies

Adding a package to `[tool.uv.workspace] members` makes it *available* but doesn't *install* it.

To install, also add to root `dependencies`:

```toml
# pyproject.toml (root)
[project]
dependencies = ["every", "everybase", "every-pv"]  # ← add here

[tool.uv.workspace]
members = ["abc/every", "abc/everybase", "std/every_pv"]  # ← and here
```

## VS Code / Pylance

When adding new packages, update `.vscode/settings.json`:

```json
"python.analysis.extraPaths": [
  "abc/every/src",
  "abc/everybase/src",
  "std/every_pv/src"  // ← add new packages
]
```

Then reload VS Code window.

## Package Naming

| Context | Style | Example |
|---------|-------|---------|
| Directory | underscore | `std/every_pv/` |
| Import | underscore | `from every_pv import ...` |
| PyPI name | hyphen | `every-pv` |
| pyproject.toml name | hyphen | `name = "every-pv"` |

## isort First-Party

When adding packages, update root `pyproject.toml`:

```toml
[tool.ruff.lint.isort]
known-first-party = ["every", "everybase", "every_pv"]  # ← underscore
```
