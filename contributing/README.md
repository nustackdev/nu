# Contributing

Quick reference for contributors.

## Docs

- [STRUCTURE.md](STRUCTURE.md) - Project layout
- [WORKFLOW.md](WORKFLOW.md) - Commands and dev flow
- [PACKAGES.md](PACKAGES.md) - Adding new packages
- [TEMPLATES.md](TEMPLATES.md) - pyproject.toml templates
- [TESTING.md](TESTING.md) - Test conventions

## Quick Start

```bash
make sync    # install everything
make test    # run tests
make format  # fix lint issues
```

## Core Packages (abc/)

| Package | Purpose |
|---------|---------|
| `every` | Protocols - Term, Flow, Ref |
| `everybase` | Base implementations - types, computations |

## Other Locations

| Dir | Purpose |
|-----|---------|
| `std/` | Standard library (every_datetime, etc.) |
| `pkgs/` | Extensions (every_notion, etc.) |
