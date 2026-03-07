# Contributing

Quick reference for contributors.

## Docs

- [STRUCTURE.md](STRUCTURE.md) - Project layout
- [WORKFLOW.md](WORKFLOW.md) - Commands and dev flow
- [PACKAGES.md](PACKAGES.md) - Adding new packages
- [TEMPLATES.md](TEMPLATES.md) - pyproject.toml templates
- [TESTING.md](TESTING.md) - Test conventions
- [GOTCHAS.md](GOTCHAS.md) - Non-obvious things

## Quick Start

```bash
make sync    # install everything
make test    # run tests
make format  # fix lint issues
```

## Core Package (src/everybase/)

| Subpackage | Purpose |
|------------|---------|
| `everybase.core` | Kernel — Term, Flow, Span, Context, Ref, Sentinel |
| `everybase.abc` | Toolbox — types, values, morphisms, flows |
| `everybase.shape` | Document topology — shapes, slots, refs |
| `everybase.table` | Relational topology (stub) |
| `everybase.graph` | Graph topology (stub) |

## Extensions (ext/)

| Package | Purpose |
|---------|---------|
| `eb-pv` | PV adapter — refs over KV storages |
| `eb-dict` | Dict adapter — plain Python dicts |
| `eb-datetime` | Datetime types |
| `eb-math` | Math types |
| `eb-fin` | Financial types |
| `eb-path` | Path type |
| `eb-uuid` | UUID type |
| `eb-shape-lens` | Terminal shape viewer |
| `eb-tree-view` | HTML tree explorer |
