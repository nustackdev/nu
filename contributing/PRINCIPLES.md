# Principles Setup Plan

This document outlines the recommended structure for the everybase Python monorepo with UV workspace.

## Directory Structure

```text
everybase/
├── pyproject.toml              # Root: UV workspace + centralized tooling
├── uv.lock                     # Workspace-wide lockfile (generated)
├── Makefile                    # Multi-package workflow
├── README.md                   # Project overview
│
├── abc/                        # CORE packages (primitives, fundamentals)
│   └── every/                  # The core "every" package
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/
│       │   └── every/
│       │       └── __init__.py
│       └── tests/
│           └── test_*.py
│
├── std/                        # STANDARD library packages
│   └── every_<name>/           # e.g., every_datetime, every_numeric
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/
│       │   └── every_<name>/
│       │       └── __init__.py
│       └── tests/
│           └── test_*.py
│
├── pkgs/                       # EXTENSION packages (integrations, optional)
│   └── every_<name>/           # e.g., every_notion, every_airtable
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/
│       │   └── every_<name>/
│       │       └── __init__.py
│       └── tests/
│           └── test_*.py
│
├── tests/                      # INTEGRATION tests (cross-package)
│   ├── conftest.py
│   └── integration/
│       └── test_*.py
│
└── docs/                       # Documentation
    └── repo/
        └── MONOREPO_SETUP.md   # This file
```

---

## 1. Root pyproject.toml

The root `pyproject.toml` serves three purposes:

1. **UV workspace definition** - declares all member packages
2. **Shared dev dependencies** - pytest, ruff, pre-commit
3. **Centralized tool config** - ruff, pytest, coverage, mypy

---

## 2. Per-Package pyproject.toml Template

Each package in `abc/`, `std/`, `pkgs/` has its own minimal `pyproject.toml`

---

## 4. Tests

- centralized cross pkg tests at root tests/
- per repo tests at {repo}/tests

---

## 5. Docs

- Per-Package README.md
- centralized docs at root docs/

---

## 6. Extra Assets

- central contributing.md, policy, license
- pkgs inherit these
