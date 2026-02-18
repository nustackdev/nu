# Workflow

## Setup

```bash
# First time
make sync       # Creates .venv, installs all packages
make dev        # Also installs pre-commit hooks
```

## Daily Commands

```bash
# Testing
make test               # Run all tests
make test-pkg PKG=everybase      # Run specific package tests
make test-fast          # Skip slow tests, fail fast

# Code quality
make lint               # Check for issues
make format             # Auto-fix issues
make check              # Both (for CI)

# Info
make list               # Show all packages
make help               # All commands
```

## Adding Dependencies

```bash
# Add to specific package
cd packages/everypv
uv add attrs

# Add dev dependency (workspace-wide)
uv add --dev pytest-mock

# Sync after changes
uv sync
```

## Building

```bash
make build PKG=everybase  # Build one package
```

## Pre-commit

Runs automatically on commit:

- Ruff lint + format
- File checks (yaml, json, trailing whitespace)

Skip with `--no-verify` (not recommended).

## CI

```bash
make ci  # Same as CI runs: check + test-cov
```
