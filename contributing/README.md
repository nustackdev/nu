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

## Core Packages (core/)

| Package | Purpose |
|---------|---------|
| `everyabc` | Protocols - Term, Flow, Ref |
| `everybase` | Base implementations - types, computations |

## Packages (packages/)

| Package | Purpose |
|---------|---------|
| `every-pv` | PV storage adapter + views |
| `every-flow` | Flow primitives |
| `every-type` | Extended type refs |
| `every-adapters` | Storage/codec backends |
| `every-notion` | Notion integration |
