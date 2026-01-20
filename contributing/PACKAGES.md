# Adding Packages

## 1. Create Structure

Pick the right tier:

- `abc/` - Core (no external deps)
- `std/` - Standard (depends on every)
- `pkgs/` - Extensions (external integrations)

```bash
mkdir -p std/every_foo/{src/every_foo,tests}
touch std/every_foo/{pyproject.toml,README.md}
touch std/every_foo/src/every_foo/__init__.py
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
dependencies = ["every"]

[tool.hatch.build.targets.wheel]
packages = ["src/every_foo"]
```

## 3. Register in Workspace

Edit root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    "abc/every",
    "std/every_foo",  # Add here
]
```

If other packages depend on it:

```toml
[tool.uv.sources]
every = { workspace = true }
every-foo = { workspace = true }  # Add here
```

## 4. Sync

```bash
uv sync
```

## Naming

| Package name | Import name | PyPI name |
|--------------|-------------|-----------|
| `every_foo` | `every_foo` | `every-foo` |

Use underscores in dirs/imports, hyphens in PyPI names.

## Dependencies

- Core (`abc/`) should have minimal deps
- Standard (`std/`) depends on `every`
- Extensions (`pkgs/`) can have external deps
