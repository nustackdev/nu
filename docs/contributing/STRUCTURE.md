# Project Structure

UV workspace monorepo. One core package + extensions.

## Layout

```text
everybase/
├── pyproject.toml          # Workspace root (not a package)
├── uv.lock                 # Lockfile (generated)
│
├── src/everybase/          # Unified core package
│   ├── core/               #   Kernel: Term, Flow, Span, Context, Sentinel
│   ├── abc/                #   Toolbox: types, values, morphisms, flows
│   ├── tree/               #   Immutable tree nodes
│   ├── meta/               #   Tree meta-tools (walk, query, transform)
│   ├── shape/              #   Document topology (shapes, slots, refs)
│   ├── table/              #   Relational topology (stub)
│   └── graph/              #   Graph topology (stub)
│
├── ext/                    # Extension packages (eb-* prefix)
│   ├── eb-pv/              #   PV adapter (refs over KV storages)
│   ├── eb-dict/            #   Dict adapter (plain Python dicts)
│   ├── eb-datetime/        #   Datetime types
│   ├── eb-math/            #   Math types (Decimal, Fraction, complex)
│   ├── eb-fin/             #   Financial types (Percentage, BasisPoint)
│   ├── eb-path/            #   Path type
│   ├── eb-uuid/            #   UUID type
│   ├── eb-shape-lens/      #   Terminal shape viewer
│   └── eb-tree-view/       #   HTML tree explorer
│
├── tests/                  # Tests for core + adapters
├── docs/                   # Documentation
├── examples/               # Example scripts
└── .agent/                 # Agent context and tasks
```

## Package Tiers

### everybase — Unified Core

Single package, minimal deps (attrs only). Contains:

| Subpackage | Purpose | Import |
|------------|---------|--------|
| `everybase.core` | Kernel — Term, Flow, Span, Context, Ref, Sentinel | `from everybase import ...` |
| `everybase.abc` | Toolbox — types, values, morphisms, capabilities, flows | `from everybase.abc import ...` |
| `everybase.shape` | Document topology — shapes, slots, collections, reactive | `from everybase.shape import ...` |
| `everybase.table` | Relational topology (stub) | `from everybase.table import ...` |
| `everybase.graph` | Graph topology (stub) | `from everybase.graph import ...` |

`everybase.__init__` re-exports everything from `everybase.core`, so top-level imports work directly.

### ext/ — Extensions

**Adapters** wire topologies to storage backends:

| Package | Import | Purpose |
|---------|--------|---------|
| `eb-pv` | `from eb_pv import ...` | PV adapter — refs over KV storages (RocksDB, memory, text) |
| `eb-dict` | `from eb_dict import ...` | Dict adapter — shapes backed by plain Python dicts |

**Type extensions** add domain-specific types:

| Package | Import | Purpose |
|---------|--------|---------|
| `eb-datetime` | `from eb_datetime import ...` | datetime, date, time, timedelta, timezone |
| `eb-math` | `from eb_math import ...` | Decimal, Fraction, complex |
| `eb-fin` | `from eb_fin import ...` | Percentage, BasisPoint |
| `eb-path` | `from eb_path import ...` | Path |
| `eb-uuid` | `from eb_uuid import ...` | UUID |

**Tools:**

| Package | Import | Purpose |
|---------|--------|---------|
| `eb-shape-lens` | `from eb_shape_lens import ...` | Terminal data viewer for Shapes |
| `eb-tree-view` | `from eb_tree_view import ...` | Interactive HTML tree explorer |

## Dependency Graph

```
everybase (kernel + toolbox + topologies)
  ├── eb-pv (PV adapter, depends on virtuals-py)
  ├── eb-dict (dict adapter, no external deps)
  └── eb-* (type extensions, tools)
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` (root) | Workspace config, tooling (ruff, pytest) |
| `src/pyproject.toml` | everybase package metadata |
| `ext/<pkg>/pyproject.toml` | Extension package metadata |
| `tests/` | Tests for everybase core + adapters |
| `ext/<pkg>/tests/` | Extension-specific tests |

## Naming Convention

All extensions use the `eb-*` prefix:

| Directory | Import | PyPI name |
|-----------|--------|-----------|
| `ext/eb-pv/` | `from eb_pv import ...` | `eb-pv` |
| `ext/eb-math/` | `from eb_math import ...` | `eb-math` |
