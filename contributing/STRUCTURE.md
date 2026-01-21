# Project Structure

UV workspace monorepo. Multiple Python packages in one repo.

## Layout

```text
everybase/
├── pyproject.toml      # Workspace root (not a package)
├── Makefile            # Dev commands
├── uv.lock             # Lockfile (generated)
│
├── abc/                # Core packages
│   ├── every/          # Protocols/contracts
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── src/every/
│   │   └── tests/
│   │
│   └── everybase/      # Base implementations
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/everybase/
│       └── tests/
│
├── std/                # Standard library packages
│   └── every_<name>/   # e.g., every_datetime
│       └── ...
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

Fundamental packages. Minimal deps.

| Package | Purpose | Depends on |
|---------|---------|------------|
| `every` | Protocols - Term, Flow, Ref, Sentinel | attrs |
| `everybase` | Base implementations - Python types, computations | every |

### std/ - Standard

Type extensions. Depends on `every` + `everybase`.

- `every_datetime` - Date/time types
- `every_numeric` - Decimal, Fraction

### pkgs/ - Extensions

External integrations. May have heavy deps.

- `every_notion` - Notion API
- `every_kv` - Key-value stores

## Dependency Graph

```
every (protocols)
  └── everybase (base impl)
        ├── std/* (type extensions)
        └── pkgs/* (integrations)
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` (root) | Workspace config, tooling (ruff, pytest) |
| `<pkg>/pyproject.toml` | Package metadata, deps |
| `<pkg>/src/<name>/` | Source code |
| `<pkg>/tests/` | Package tests |
