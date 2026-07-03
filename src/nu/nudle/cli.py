"""`nudle` CLI -- `run` and `dev` modes for nudle apps.

Module convention (the file you pass to `nudle run` / `nudle dev`):

- `app: nu.Nu`            (required)  per-session UI program. One eval per
                                      websocket connection, with a fresh
                                      NudleSession bound on ctx. Combine
                                      multiple flows with `|`.
- `bg: nu.Nu`             (optional)  process-scoped background program.
                                      One eval per server process, no
                                      session bound. For things that touch
                                      persistent state (rocksdb counters,
                                      queue consumers, periodic jobs).
                                      Combine with `|` if you need many.
- `context` or `ctx`      (required)  a `nu.Context`, or a callable
                                      returning a sync/async context
                                      manager yielding one.

Static assets resolve automatically: in a wheel install, the compiled web
bundle ships as `nudle/_static` and is served at `/`. In an editable install
that path is missing, only `/ws` is served, and you run vite separately.

Run modes:

- `nudle run <file>`              one-shot; serves until Ctrl-C
- `nudle dev <file>`              parent watches files, child runs the server;
                                  on change the child is restarted. The
                                  browser auto-reconnects and gets a fresh
                                  mount payload, so no protocol changes
                                  needed for hot reload.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import importlib.util
import signal
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import nu
import uvicorn

from .serve import build_fastapi_app


if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from types import ModuleType


__all__ = ["main"]


def _load_module(file_path: Path) -> ModuleType:
    if not file_path.exists():
        raise FileNotFoundError(f"no such file: {file_path}")
    parent = str(file_path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot build import spec for {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@contextlib.asynccontextmanager
async def _enter_context(value: object) -> AsyncIterator[nu.Context]:
    """Normalize the `context` module attr into an async CM yielding nu.Context."""
    if isinstance(value, nu.Context):
        yield value
        return
    if not callable(value):
        raise RuntimeError("module.context must be a nu.Context or a callable")
    cm = value()
    if isinstance(cm, nu.Context):
        yield cm
        return
    if hasattr(cm, "__aenter__"):
        async with cm as ctx:  # type: ignore[union-attr]
            yield ctx
        return
    if hasattr(cm, "__enter__"):
        with cm as ctx:  # type: ignore[union-attr]
            yield ctx
        return
    raise RuntimeError("module.context() must return a Context or a context manager")


async def _serve_module(mod: ModuleType, host: str, port: int) -> None:
    app = getattr(mod, "app", None)
    if app is None:
        raise RuntimeError(f"{mod.__name__}: no module-level `app`")
    ctx_value = getattr(mod, "context", None)
    if ctx_value is None:
        ctx_value = getattr(mod, "ctx", None)
    if ctx_value is None:
        raise RuntimeError(f"{mod.__name__}: no module-level `context` (or `ctx`)")
    bg = getattr(mod, "bg", None)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    async with _enter_context(ctx_value) as ctx:
        bg_tasks = (
            [asyncio.create_task(nu.arun(bg, ctx), name="bg")] if bg is not None else []
        )
        fastapi_app = build_fastapi_app(app, ctx)
        config = uvicorn.Config(fastapi_app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        # Uvicorn installs its own signal handlers; turn that off so our
        # stop event is the single shutdown source.
        config.install_signal_handlers = False
        serve_task = asyncio.create_task(server.serve(), name="uvicorn")
        stop_task = asyncio.create_task(stop.wait(), name="stop")
        try:
            done, _ = await asyncio.wait(
                {serve_task, stop_task, *bg_tasks},
                return_when=asyncio.FIRST_COMPLETED,
            )
            # Surface bg / serve exceptions (don't swallow).
            for t in done:
                if t is stop_task:
                    continue
                exc = t.exception()
                if exc is not None and not isinstance(exc, asyncio.CancelledError):
                    raise exc
        finally:
            server.should_exit = True
            for t in bg_tasks:
                if not t.done():
                    t.cancel()
            for t in (*bg_tasks, serve_task):
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass
            stop_task.cancel()


def _do_run(file: str, host: str, port: int) -> None:
    mod = _load_module(Path(file).resolve())
    asyncio.run(_serve_module(mod, host, port))


def _do_dev(file: str, host: str, port: int, watch: list[str] | None) -> None:
    try:
        from watchfiles import watch as watch_files
    except ImportError as e:
        raise RuntimeError(
            "watchfiles not installed; install nudle with the dev extra or add watchfiles",
        ) from e

    file_path = Path(file).resolve()
    extra = [Path(p).resolve() for p in (watch or [])]
    watch_paths = [file_path, *extra]
    sys.stderr.write(f"[nudle dev] watching: {', '.join(str(p) for p in watch_paths)}\n")

    cmd = [
        sys.executable,
        "-m",
        "nudle",
        "run",
        str(file_path),
        "--host",
        host,
        "--port",
        str(port),
    ]

    def spawn() -> subprocess.Popen[bytes]:
        sys.stderr.write("[nudle dev] starting...\n")
        return subprocess.Popen(cmd)  # noqa: S603

    def stop(proc: subprocess.Popen[bytes]) -> None:
        if proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    child = spawn()
    try:
        for changes in watch_files(*watch_paths):
            paths = ", ".join(p for _, p in changes)
            sys.stderr.write(f"[nudle dev] change: {paths}\n")
            stop(child)
            child = spawn()
    except KeyboardInterrupt:
        pass
    finally:
        stop(child)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="nudle")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("run", "dev"):
        p = sub.add_parser(name, help=f"{name} a nudle app")
        p.add_argument("file", help="path to the python module exposing `app` and `context`")
        p.add_argument("--host", default="127.0.0.1")
        p.add_argument("--port", type=int, default=8080)
        if name == "dev":
            p.add_argument(
                "--watch",
                action="append",
                default=None,
                help="extra path to watch; repeatable",
            )
    args = parser.parse_args(argv)
    if args.cmd == "run":
        _do_run(args.file, args.host, args.port)
    elif args.cmd == "dev":
        _do_dev(args.file, args.host, args.port, args.watch)


if __name__ == "__main__":
    main()
