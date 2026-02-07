# Project Structure

UV workspace monorepo. Multiple Python packages in one repo.

## Layout

```text
everybase/
├── pyproject.toml          # Workspace root (not a package)
├── Makefile                # Dev commands
├── uv.lock                 # Lockfile (generated)
│
├── src/everybase/          # Core package (everybase)
│   ├── pyproject.toml
│   ├── src/everybase/
│   └── tests/
│
├── substrates/             # Integration substrates
│   ├── eb-shape/    #   eb_shape (hierarchical, uniform CRUD)
│   ├── eb-service/  #   eb_service (flat RPC)
│   ├── eb-table/    #   eb_table (relational)
│   ├── eb-rest/     #   eb_rest (HTTP, CRUD + actions)
│   ├── eb-stream/   #   eb_stream (event streams)
│   └── eb-gql/      #   eb-gql (GraphQL)
│
├── pkgs/                   # Utility + extension packages
│   ├── eb-pv/       #   PV storage substrate
│   ├── eb-dict/     #   Dict substrate
│   ├── eb-flow/     #   Flow primitives
│   ├── eb-flow-ext/ #   Flow extensions
│   ├── eb-notion/   #   Notion integration
│   └── ...                 #   datetime, math, fin, path, uuid
│
├── docs/                   # Documentation
│   └── contributing/
├── examples/               # Example scripts
│
└── tests/                  # Integration tests
```

## Package Tiers

### everybase — Foundation

The unified core package. Minimal deps. Contains two subpackages:

| Subpackage | Purpose | Import |
|------------|---------|--------|
| `everybase.core` | Protocols - Term, Flow, Ref, Model, Sentinel | `from everybase import ...` |
| `everybase.abc` | Base implementations - Python types, computations | `from everybase.abc import ...` |

`everybase.__init__` re-exports everything from `everybase.core`, so top-level imports work directly.

### pkg-* — Everything Else

Models, substrates, extensions, and integrations.

| Directory | Package | Purpose |
|-----------|---------|---------|
| `eb-shape` | `eb_shape` | Document model - shapes, slots, items, collections |
| `eb-table` | `eb_table` | Relational model - tables, columns, queries |
| `eb-pv` | `eb-pv` | PV storage substrate + views + adapters |
| `eb-dict` | `eb-dict` | Dict substrate (plain nested dicts, no persistence) |
| `eb-flow` | `eb-flow` | Flow primitives (Seq, If, While, etc.) |
| `eb-flow-ext` | `eb-flow-ext` | Flow extensions (cancellation, progress) |
| `pkg-every-stdtypes` | `every-type` | Extended type refs (Date, Decimal, UUID, etc.) |
| `eb-notion` | `eb-notion` | Notion API integration |

## Dependency Graph

```
everybase (contracts + base impl)
  ├── eb_shape (document model)
  │     ├── eb-pv (PV substrate + views)
  │     └── eb-dict (dict substrate)
  └── eb_table (relational model)
        └── eb-notion, etc.
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
| Directory | `pkg-` prefix | `eb-pv/` |
| Import | underscore | `from eb_pv import ...` |
| PyPI name | hyphen | `eb-pv` |
| pyproject.toml name | hyphen | `name = "eb-pv"` |
