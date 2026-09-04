"""Forced-mode variants of Parallel: threaded and async placement.

- ``ParallelThreaded`` under async drive - every child on a worker thread.
- ``ParallelAsync`` under async drive - every child on the loop.
- ``ParallelAsync`` under sync ``run`` - refused up front as async-only.
- ``ParallelThreaded`` over a subtree with an async-only atom - rejected
  by the compile-time ``parallel_threaded_no_async_only_child`` law.
- ``ParallelAsync`` over a subtree with a sync-only atom - rejected by
  ``parallel_async_no_sync_only_child``.
"""

from __future__ import annotations

import threading

import pytest
from _support.async_atoms import AsyncOnlyAction, RunsAnywhereAction, SyncOnlyAction

from nu.core.flows import ParallelAsync, ParallelThreaded
from nu.engine.validation import ValidationError
from nu.lang.helpers import arun, compile, run, validate


def _this_thread() -> str:
    return threading.current_thread().name


def _is_worker(name: str) -> bool:
    return name.startswith("nu-worker")


async def test_parallel_threaded_places_every_child_off_the_loop() -> None:
    # Both children are runs-anywhere; under Threaded they must both land on
    # worker threads regardless of the smart choice.
    _, ctx = await arun(
        ParallelThreaded(RunsAnywhereAction("a"), RunsAnywhereAction("b")),
        max_parallel=2,
    )
    assert _is_worker(ctx.attrs["a"])
    assert _is_worker(ctx.attrs["b"])


async def test_parallel_async_places_every_child_on_the_loop() -> None:
    loop = _this_thread()
    _, ctx = await arun(
        ParallelAsync(RunsAnywhereAction("a"), RunsAnywhereAction("b")),
        max_parallel=2,
    )
    assert ctx.attrs["a"] == loop
    assert ctx.attrs["b"] == loop


def test_parallel_async_sync_run_is_rejected_as_async_only() -> None:
    with pytest.raises(RuntimeError):
        run(ParallelAsync(RunsAnywhereAction("a")))


def test_parallel_threaded_rejects_async_only_child_at_compile_time() -> None:
    program = compile(ParallelThreaded(AsyncOnlyAction("a")))
    with pytest.raises(ValidationError, match="parallel_threaded_no_async_only_child"):
        validate(program)


def test_parallel_async_rejects_sync_only_child_at_compile_time() -> None:
    program = compile(ParallelAsync(SyncOnlyAction("a")))
    with pytest.raises(ValidationError, match="parallel_async_no_sync_only_child"):
        validate(program)
