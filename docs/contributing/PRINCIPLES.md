# Principles Setup Plan

This document outlines the principles for the everybase Python monorepo with UV workspace.

## 1. Root pyproject.toml

The root `pyproject.toml` serves three purposes:

1. **UV workspace definition** - declares all member packages
2. **Shared dev dependencies** - pytest, ruff, pre-commit
3. **Centralized tool config** - ruff, pytest, coverage, mypy

---

## 2. Per-Package pyproject.toml Template

Each package in `everybase/`, `packages/` has its own minimal `pyproject.toml`

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
