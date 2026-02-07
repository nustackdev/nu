# Adding Packages

## 1. Create Structure

```bash
mkdir -p packages/every-foo/{src/every_foo,tests}
touch packages/every-foo/{pyproject.toml,README.md}
touch packages/every-foo/src/every_foo/__init__.py
```

## 2. Create pyproject.toml

See [TEMPLATES.md](TEMPLATES.md) for full template.

Minimal:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "every-foo"
version = "0.1.0"
description = "Foo for every"
requires-python = ">=3.10"
dependencies = ["everybase"]

[tool.hatch.build.targets.wheel]
packages = ["src/every_foo"]
```

## 3. Register in Workspace

Edit root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    "everybase",
    "packages/every-foo",  # Add here
]
```

If other packages depend on it:

```toml
[tool.uv.sources]
everybase = { workspace = true }
every-foo = { workspace = true }  # Add here
```

## 4. Sync

```bash
uv sync
```

## Naming

| Directory name | Import name | PyPI name |
|----------------|-------------|-----------|
| `every-foo` | `every_foo` | `every-foo` |

Use hyphens in directory names, underscores in imports/package dirs, hyphens in PyPI names.

## Dependencies

- Core (`everybase/`) should have minimal deps
- Packages (`packages/`) depend on everybase and may have external deps
