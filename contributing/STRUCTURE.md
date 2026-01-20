# Project Structure

UV workspace monorepo. Multiple Python packages in one repo.

## Layout

```
everybase-2/
├── pyproject.toml      # Workspace root (not a package)
├── Makefile            # Dev commands
├── uv.lock             # Lockfile (generated)
│
├── abc/                # Core packages
│   └── every/          # The "every" package
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/every/
│       └── tests/
│
├── std/                # Standard library packages
│   └── every_<name>/   # e.g., every_datetime
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/every_<name>/
│       └── tests/
│
├── pkgs/               # Extensions/integrations
│   └── every_<name>/   # e.g., every_notion
│       └── ...
│
├── tests/              # Integration tests
│   └── integration/
│
└── contributing/       # This docs
```

## Package Tiers

### abc/ - Core
Fundamental abstractions. Zero or minimal deps.
- `every` - Term, Flow, Ref, Sentinel

### std/ - Standard
Type extensions and utilities. Depends on `every`.
- `every_datetime` - Date/time types
- `every_numeric` - Decimal, Fraction

### pkgs/ - Extensions
External integrations. May have heavy deps.
- `every_notion` - Notion API
- `every_kv` - Key-value stores

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` (root) | Workspace config, tooling (ruff, pytest) |
| `<pkg>/pyproject.toml` | Package metadata, deps |
| `<pkg>/src/<name>/` | Source code |
| `<pkg>/tests/` | Package tests |
