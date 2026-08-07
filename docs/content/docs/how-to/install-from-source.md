---
title: Install from source
---

Clone Nu and work off the tree. For a normal install, see [Install](install).

## Prerequisites

- Python 3.10 or later.
- Node 20 or later, if you plan to build the UI bundle.

## Clone and sync

```bash
git clone https://github.com/nustackdev/nu
cd nu
make sync
```

`make sync` runs `uv sync`, which creates `.venv/` and installs base deps + dev tooling (ruff, pytest, pre-commit) in one shot. Nothing outside this repo is required.

## Run commands

Two options, pick either:

- **`uv run <cmd>`.** Uses `.venv/` automatically, no activation needed.
- **`source .venv/bin/activate`.** Activates the venv in your shell; then run `python`, `pytest`, etc. directly.

## Pull the full stack as editable siblings

If you want `nu.v` (virtuals + RocksDB), `nu.invisibles`, and the rest of the fabrics as editable installs from sibling repos, clone them next to `nu/` and add `--group local`:

```bash
cd ..
git clone https://github.com/nustackdev/virtuals
git clone https://github.com/nustackdev/invisibles
git clone https://github.com/nustackdev/kh57
cd nu
uv sync --group local
```

Without the siblings, `--group local` fails with `Distribution not found at: file:///.../virtuals`. Drop the flag for the lean install, or clone the missing repos.

## Build the UI bundle

Skip if you are not using UI.

```bash
make web-install
make web-build
```

`web-install` runs `npm install` across the UI workspace (`core`, `kit`, `nudle`). `web-build` compiles the vite bundle into `src/nu/ui/nudle/dist/`. The `nudle` Python package picks the bundle up through a symlink; no extra wiring.

For UI hacking, run the vite dev server instead of the build:

```bash
make web-dev
```

Vite serves the app on `http://localhost:5173`, proxies `/ws` to the FastAPI backend on `:8080`, and hot-reloads on file changes.

## Verify

```bash
uv run python -c "import nu; print(nu.__version__)"
```

Run the counter dashboard example:

```bash
uv run python examples/counter.py
```

Open the browser tab that appears. The counter ticks once a second; the dashboard mirrors it live.

## Common errors

**`uv: command not found` after `make sync`.** `make install` puts uv at `~/.local/bin/uv`. Add that to your `PATH`, or open a new shell.

**`Distribution not found at: file:///.../virtuals` on `uv sync --group local`.** The `local` group pulls the full stack as editable installs from sibling repos. Clone `virtuals`, `invisibles`, and `kh57` as siblings of `nu/` (see [Pull the full stack](#pull-the-full-stack-as-editable-siblings)), or drop `--group local`.

**Browser shows 404 on `/`.** The web bundle is not built. Run `make web-build`.

**`import nudle` resolves to a module, not the ui wheel package.** A local `nudle.py` on `sys.path` shadows the package. Rename that file, or run from a directory that does not shadow it.
