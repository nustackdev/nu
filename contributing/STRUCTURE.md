# Project Structure

UV workspace monorepo. Multiple Python packages in one repo.

## Layout

```text
everybase/
├── pyproject.toml      # Workspace root (not a package)
├── Makefile            # Dev commands
├── uv.lock             # Lockfile (generated)
│
├── core/               # Core packages
│   ├── everyabc/       # Protocols/contracts
│   │   ├── pyproject.toml
│   │   ├── src/everyabc/
│   │   └── tests/
│   │
│   └── everybase/      # Base implementations
│       ├── pyproject.toml
│       ├── src/everybase/
│       └── tests/
│
├── packages/           # All other packages
│   └── every-<name>/   # e.g., every-pv, every-flow
│       ├── pyproject.toml
│       ├── src/every_<name>/
│       └── tests/
│
├── tests/              # Integration tests
│   └── integration/
│
└── contributing/       # This docs
```

## Package Tiers

### core/ - Foundation

Fundamental packages. Minimal deps.

| Package | Purpose | Depends on |
|---------|---------|------------|
| `everyabc` | Protocols - Term, Flow, Ref, Sentinel | (none) |
| `everybase` | Base implementations - Python types, computations | everyabc |

### packages/ - Everything Else

Models, extensions, and integrations. Depends on core.

| Package | Purpose |
|---------|---------|
| `every-shape` | Document model (hierarchical shapes) |
| `every-pv` | PV storage adapter + views |
| `every-flow` | Flow primitives (Seq, If, While, etc.) |
| `every-flow-ext` | Flow extensions (cancellation, progress) |
| `every-type` | Extended type refs (Date, Decimal, UUID, etc.) |
| `every-kv` | Key-value store protocol |
| `every-adapters` | Storage/codec/observer backends |
| `every-notion` | Notion API integration |

## Dependency Graph

```
everyabc (contracts)
  └── everybase (base impl)
        ├── packages/* (models, extensions, integrations)
        └── ...
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` (root) | Workspace config, tooling (ruff, pytest) |
| `<pkg>/pyproject.toml` | Package metadata, deps |
| `<pkg>/src/<name>/` | Source code |
| `<pkg>/tests/` | Package tests |

## Naming Convention

| Context | Style | Example |
|---------|-------|---------|
| Directory | hyphen | `packages/every-pv/` |
| Import | underscore | `from every_pv import ...` |
| PyPI name | hyphen | `every-pv` |
| pyproject.toml name | hyphen | `name = "every-pv"` |
