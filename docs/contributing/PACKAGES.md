# Adding Packages

## 1. Create Structure

For a core package:
```bash
mkdir -p core/everyfoo/{src/everyfoo,tests}
touch core/everyfoo/{pyproject.toml,README.md}
touch core/everyfoo/src/everyfoo/__init__.py
```

For an optional extension package:
```bash
mkdir -p pkgs/eb-foo/{src/eb_foo,tests}
touch pkgs/eb-foo/{pyproject.toml,README.md}
touch pkgs/eb-foo/src/eb_foo/__init__.py
```

## 2. Create pyproject.toml

See [TEMPLATES.md](TEMPLATES.md) for full template.

Minimal:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "everyfoo"  # or "eb-foo" for pkgs/
version = "0.1.0"
description = "Foo for everybase"
requires-python = ">=3.10"
dependencies = ["everybase"]

[tool.hatch.build.targets.wheel]
packages = ["src/everyfoo"]  # or ["src/eb_foo"]
```

## 3. Register in Workspace

Edit root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    "core/everyfoo",  # Add here (or "pkgs/eb-foo")
]
```

If other packages depend on it:

```toml
[tool.uv.sources]
everyfoo = { workspace = true }  # Add here
```

## 4. Sync

```bash
uv sync
```

## Naming

| Tier | Directory | Import | PyPI name |
|------|-----------|--------|-----------|
| Core | `core/everyfoo/` | `everyfoo` | `everyfoo` |
| Pkg | `pkgs/eb-foo/` | `eb_foo` | `eb-foo` |

Use hyphens in directory/PyPI names, underscores in import names.

## Dependencies

- Core (`core/`) packages should have minimal deps
- Extension packages (`pkgs/`) depend on everybase and may have external deps
