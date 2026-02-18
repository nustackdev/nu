# Project Structure

UV workspace monorepo. Multiple Python packages in one repo.

## Layout

```text
everybase/
├── pyproject.toml          # Workspace root (not a package)
├── Makefile                # Dev commands
├── uv.lock                 # Lockfile (generated)
│
├── core/                   # Core packages (every* prefix)
│   ├── everybase/          #   Foundation: contracts + base implementations
│   │   ├── pyproject.toml
│   │   ├── src/everybase/
│   │   └── tests/
│   ├── everyshape/         #   Declarative document model (shapes, slots, refs)
│   ├── everypv/            #   Polymorphic views over KV storages
│   ├── everytable/         #   Relational data model (stub)
│   ├── everystream/        #   Push-based event streams (stub)
│   └── everygraph/         #   Graph data model (stub)
│
├── pkgs/                   # Optional extension packages (eb-* prefix)
│   ├── eb-datetime/        #   Datetime types
│   ├── eb-math/            #   Math types
│   ├── eb-fin/             #   Financial types
│   ├── eb-path/            #   Path types
│   ├── eb-uuid/            #   UUID types
│   ├── eb-shape-lens/      #   Terminal shape viewer
│   └── eb-tree-view/       #   HTML tree explorer
│
├── docs/                   # Documentation
│   └── contributing/
├── examples/               # Example scripts
│
└── .agent/                 # Agent context and tasks
```

## Package Tiers

### everybase — Foundation

The unified core package. Minimal deps. Contains two subpackages:

| Subpackage | Purpose | Import |
|------------|---------|--------|
| `everybase.core` | Protocols - Term, Flow, Ref, Model, Sentinel | `from everybase import ...` |
| `everybase.abc` | Base implementations - Python types, computations, flows | `from everybase.abc import ...` |

`everybase.__init__` re-exports everything from `everybase.core`, so top-level imports work directly.

### Core packages — Data substrates

| Package | Import | Purpose |
|---------|--------|---------|
| `everyshape` | `from everyshape import ...` | Document model - shapes, slots, items, collections |
| `everypv` | `from everypv import ...` | PV storage substrate + views + adapters |
| `everytable` | `from everytable import ...` | Relational model (stub) |
| `everystream` | `from everystream import ...` | Event streams (stub) |
| `everygraph` | `from everygraph import ...` | Graph data model (stub) |

### pkgs/ — Optional extensions

Types (`eb-datetime`, `eb-math`, `eb-fin`, `eb-path`, `eb-uuid`) and tools (`eb-shape-lens`, `eb-tree-view`).

## Dependency Graph

```
everybase (contracts + base impl)
  ├── everyshape (document model, reactive flows)
  │     └── everypv (PV substrate + views)
  └── everytable, everystream, everygraph (stubs)
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` (root) | Workspace config, tooling (ruff, pytest) |
| `<dir>/pyproject.toml` | Package metadata, deps |
| `<dir>/src/<name>/` | Source code |
| `<dir>/tests/` | Package tests |

## Naming Convention

| Tier | Directory | Import | PyPI name |
|------|-----------|--------|-----------|
| Core | `core/everyshape/` | `from everyshape import ...` | `everyshape` |
| Pkg | `pkgs/eb-math/` | `from eb_math import ...` | `eb-math` |
