# Project Structure

UV workspace monorepo. Multiple Python packages in one repo.

## Layout

```text
everybase/
├── pyproject.toml          # Workspace root (not a package)
├── Makefile                # Dev commands
├── uv.lock                 # Lockfile (generated)
│
├── core-every/             # Protocols/contracts (everyabc)
│   ├── pyproject.toml
│   ├── src/everyabc/
│   └── tests/
│
├── core-every-bases/       # Base implementations (everybase)
│   ├── pyproject.toml
│   ├── src/everybase/
│   └── tests/
│
├── pkg-every-shape/        # Document model (everyshape)
│   ├── pyproject.toml
│   ├── src/everyshape/
│   └── tests/
│
├── pkg-every-table/        # Relational model (everytable)
│   ├── pyproject.toml
│   ├── src/everytable/
│   └── tests/
│
├── pkg-every-dict/         # Dict substrate
├── pkg-every-flow/         # Flow primitives
├── pkg-every-flow-ext/     # Flow extensions
├── pkg-every-notion/       # Notion integration
├── pkg-every-pv/           # PV storage substrate
├── pkg-every-stdtypes/     # Extended type refs
│
├── _docs/                  # Documentation
│   ├── contributing/       # Dev setup, structure, conventions
│   └── hierarchy.md        # Architecture
├── _examples/              # Example scripts
│
└── tests/                  # Integration tests
```

## Package Tiers

### core-* — Foundation

Fundamental packages. Minimal deps.

| Directory | Package | Purpose | Depends on |
|-----------|---------|---------|------------|
| `core-every` | `everyabc` | Protocols - Term, Flow, Ref, Model, Sentinel | (none) |
| `core-every-bases` | `everybase` | Base implementations - Python types, computations | everyabc |

### pkg-* — Everything Else

Models, substrates, extensions, and integrations.

| Directory | Package | Purpose |
|-----------|---------|---------|
| `pkg-every-shape` | `everyshape` | Document model - shapes, slots, items, collections |
| `pkg-every-table` | `everytable` | Relational model - tables, columns, queries |
| `pkg-every-pv` | `every-pv` | PV storage substrate + views + adapters |
| `pkg-every-dict` | `every-dict` | Dict substrate (plain nested dicts, no persistence) |
| `pkg-every-flow` | `every-flow` | Flow primitives (Seq, If, While, etc.) |
| `pkg-every-flow-ext` | `every-flow-ext` | Flow extensions (cancellation, progress) |
| `pkg-every-stdtypes` | `every-type` | Extended type refs (Date, Decimal, UUID, etc.) |
| `pkg-every-notion` | `every-notion` | Notion API integration |

## Dependency Graph

```
everyabc (contracts)
  └── everybase (base impl)
        ├── everyshape (document model)
        │     ├── every-pv (PV substrate + views)
        │     └── every-dict (dict substrate)
        └── everytable (relational model)
              └── every-notion, etc.
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` (root) | Workspace config, tooling (ruff, pytest) |
| `<dir>/pyproject.toml` | Package metadata, deps |
| `<dir>/src/<name>/` | Source code |
| `<dir>/tests/` | Package tests |

## Naming Convention

| Context | Style | Example |
|---------|-------|---------|
| Directory | `core-`/`pkg-` prefix | `pkg-every-pv/` |
| Import | underscore | `from every_pv import ...` |
| PyPI name | hyphen | `every-pv` |
| pyproject.toml name | hyphen | `name = "every-pv"` |
