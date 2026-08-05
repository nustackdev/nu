---
title: Install
---

Install Nu from source. PyPI packages come later.

## Prerequisites

- Python 3.12 or later.
- [uv](https://docs.astral.sh/uv/) for the Python side. `make sync` installs it if missing.
- Node.js 20 or later with npm, for the `nu.ui` Fabric. Skip if you only need the core, `nu.m`, or `nu.v`.

## Install the Python side

Clone and sync:

```bash
git clone https://github.com/nustackdev/nu
cd nu
make sync
```

`make sync` runs `uv sync`, which provisions `.venv/` with the full stack: core, `nu.m`, `nu.v` (virtuals + RocksDB), `nu.ui` bindings, `nu.invisibles`, and `nu.ray`. For a lean install without the distributed groups, run `uv sync --no-group local`.

Activate the venv:

```bash
source .venv/bin/activate
```

Or prefix every command with `uv run`.

Verify:

```bash
uv run python -c "import nu; print(nu.__version__)"
```

## Build the UI bundle

Needed for the `nu.ui` Fabric. Skip if you are not using UI.

```bash
make web-install
make web-build
```

`web-install` runs `npm install` across the UI workspace (`core`, `kit`, `nudle`). `web-build` compiles the vite bundle into `src/nu/ui/nudle/dist/`. The `nudle` Python package (installed by `uv sync`) picks the bundle up through a symlink; no extra wiring.

For UI hacking, run the vite dev server instead of the build:

```bash
make web-dev
```

Vite serves the app on `http://localhost:5173`, proxies `/ws` to the FastAPI backend on `:8080`, and hot-reloads on file changes.

## Verify end-to-end

Run the counter dashboard example:

```bash
uv run python examples/counter.py
```

Open the browser tab that appears. The counter ticks once a second; the dashboard mirrors it live.

## Common errors

**`uv: command not found` after `make sync`.** `make install` puts uv at `~/.local/bin/uv`. Add that to your `PATH`, or open a new shell.

**Browser shows 404 on `/`.** The web bundle is not built. Run `make web-build`.

**Warning: `import nudle` resolves to a module, not the ui wheel package.** A local `nudle.py` on `sys.path` shadows the package. Rename that file, or run from a directory that does not shadow it.
