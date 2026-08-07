---
title: Cross-repo dev
---

Set up editable dev across nu and its sibling packages in one workspace. For a single-repo nu clone, see [Install from source](install-from-source).

One `.venv`, one `uv.lock`, every repo editable against every other. Edit any file in any repo, changes are live everywhere.

## Prerequisites

- git
- [uv](https://docs.astral.sh/uv/)
- Python 3.10 or later
- GitHub SSH access to `nustackdev/*` (for the siblings you want)

## The pattern

Create a small workspace repo alongside the packages you want to develop. The workspace repo holds one `pyproject.toml` that declares the siblings as uv workspace members, and one `Makefile` to bootstrap them.

Nothing about nu itself changes. This pattern layers on top of any set of uv-based Python repos.

## Layout

Clone the workspace and its siblings side by side under one parent:

```text
~/Projects/nustackdev/
    workspace/          # your workspace repo
    nu/
    virtuals/
    invisibles/
    kh57/
    nulog/
    ...
```

The workspace directory name is yours to pick. `workspace/`, `dev/`, `nustack/` all fine.

## Workspace files

Two files. Adjust the member list to the repos you actually work on.

`pyproject.toml`:

```toml
[project]
name = "nustack-workspace"
version = "0"
requires-python = ">=3.10"
dependencies = [
    "nustack-py[all]",
    "virtuals-py[rocksdb]",
    "invisibles-py",
    "kh57",
    "nulog",
]

[tool.uv.workspace]
members = ["../nu", "../virtuals", "../invisibles", "../kh57", "../nulog"]

[tool.uv.sources]
nustack-py    = { workspace = true }
virtuals-py   = { workspace = true }
invisibles-py = { workspace = true }
kh57          = { workspace = true }
nulog         = { workspace = true }
```

`Makefile`:

```makefile
.PHONY: init sync test-all lint-all

REPOS := nu virtuals invisibles kh57 nulog

init:
	@for r in $(REPOS); do \
		[ -d ../$$r ] && echo "skip ../$$r" || \
		git clone git@github.com:nustackdev/$$r.git ../$$r; \
	done

sync: init
	uv sync

test-all:
	uv run pytest $(addprefix ../,$(REPOS))

lint-all:
	uv run ruff check $(addprefix ../,$(REPOS))
```

`.gitignore` for the workspace repo:

```
/.venv/
__pycache__/
*.egg-info/
.pytest_cache/
```

## Bootstrap

From the workspace directory:

```bash
make sync
```

`make init` clones any missing siblings over SSH. `make sync` runs it, then `uv sync`. That creates `.venv/` in the workspace directory and installs every sibling as an editable workspace member. Idempotent, re-run any time.

## Common commands

```bash
make sync         # clone missing siblings + uv sync
make test-all     # pytest across all repos
make lint-all     # ruff across all repos
```

Run any tool against the shared venv with `uv run <cmd>`.

## How it works

uv workspaces resolve `[tool.uv.sources] = { workspace = true }` to the member listed under `[tool.uv.workspace] members`. Each sibling installs as editable from its local path. One lockfile pins the whole graph. Edits to any member are live in the shared venv immediately, no reinstall.

The per-repo `pyproject.toml` files stay clean. They declare their PyPI dependencies as usual, with no path sources. Fresh clones of any single repo still work standalone.
