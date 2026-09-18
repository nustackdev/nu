# nudle

The compiled web bundle for [Nu](https://nustack.dev)'s UI fabric.

This distribution carries no source of its own. The whole payload is the vite
output of the nudle SPA, shipped under `nudle/build/`. `nustd.ws_server`
resolves it at runtime as `nudle.__path__[0] / "build"` and mounts it; when the
wheel is missing the UI backend still boots headless with only `/ws`.

It is a separate distribution for one reason: the SPA is rebuilt on every UI
tweak, and folding a megabyte of bundle into `nustd` each time would eat the
PyPI project quota. Splitting it keeps the fabric wheel small and lets the
bundle move on its own version clock.

## Install

You do not install this directly. `nustd[ui]` depends on it:

```bash
pip install "nustd[ui]"
```

## Source

The app lives in the repo's npm workspace at `pkgs/ts/nudle`, beside the two
packages it builds on, `@nustackdev/ui-core` and `@nustackdev/ui-kit`.
`make web-build` produces `pkgs/ts/nudle/dist`, which this wheel
force-includes at `nudle/build/`.

The version here and in `pkgs/ts/nudle/package.json` are bumped together.

Docs at [nustack.dev](https://nustack.dev).
