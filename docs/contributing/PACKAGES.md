# Adding Packages

Topologies (shape, table, graph) live inside `everybase` itself.
Extensions (adapters, types, tools) live in `ext/`.

## Adding a Topology

Topologies are subpackages of everybase. Add directly to `src/everybase/`:

```bash
mkdir -p src/everybase/foo
touch src/everybase/foo/__init__.py
```

No pyproject.toml needed — it's part of the everybase package.

## Adding an Extension

```bash
mkdir -p ext/eb-foo/{src/eb_foo,tests}
touch ext/eb-foo/{pyproject.toml,README.md}
touch ext/eb-foo/src/eb_foo/__init__.py
```

### Create pyproject.toml

See [TEMPLATES.md](TEMPLATES.md) for full template.

Minimal:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "eb-foo"
version = "0.1.0"
description = "Foo for everybase"
requires-python = ">=3.10"
dependencies = ["everybase>=0.1.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/eb_foo"]
```

### Register in Workspace

Edit root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    "ext/eb-foo",
]

[tool.uv.sources]
eb-foo = { workspace = true }
```

### Sync

```bash
uv sync
```

## Naming

All extensions use the `eb-*` prefix:

| Directory | Import | PyPI name |
|-----------|--------|-----------|
| `ext/eb-foo/` | `eb_foo` | `eb-foo` |

Use hyphens in directory/PyPI names, underscores in import names.

## Dependencies

- `everybase` has minimal deps (attrs only)
- Extensions depend on `everybase` and may have external deps
- Adapters (eb-virtuals, eb-dict) bridge topologies to storage backends
- Type extensions add domain-specific types with no storage assumptions
