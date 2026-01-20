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

## Package Locations

| Dir | Purpose |
|-----|---------|
| `abc/` | Core primitives |
| `std/` | Standard library |
| `pkgs/` | Extensions/integrations |
