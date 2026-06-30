"""End-to-end eval-modes tests: real trees, real compile, real drive.

Where ``test_runtime.py`` unit-tests the Runtime methods against hand-written
``_fake_program`` thunks, this file drives **real** Nu programs through the full
pipeline - ``compile`` (so the ``on_loop`` attribute is genuinely synthesized) →
``validate`` → drive - and asserts the placement decisions described in
``projects/nu/model/04-attributes/03-eval-modes.md`` actually happen.

Placement is observed by where an atom runs: each async-class test atom records
``threading.current_thread().name``. An async-on-loop atom runs on the caller's
loop thread; a sync-offloaded atom runs on a ``nu-worker`` pool thread. The
test atoms raise on their wrong path, so a misplacement fails loudly rather than
passing silently.

Each test names the worked example from the doc it mirrors.
"""

from __future__ import annotations

import threading

import pytest
from _support.async_atoms import (
    AsyncOnlyAction,
    RunsAnywhereAction,
    SyncOnlyAction,
)

from nu.flows import Parallel, Sequential
from nu.lang.helpers import arun, run


def _this_thread() -> str:
    return threading.current_thread().name


def _is_worker(name: str) -> bool:
    return name.startswith("nu-worker")


# --- the top diamond: does the tree need a loop? --------------------------


def test_pure_tree_runs_sync_on_the_caller_thread() -> None:
    # "no async-only anywhere -> no loop": runs on the call stack, caller thread.
    caller = _this_thread()
    _, ctx = run(Sequential(RunsAnywhereAction("a"), RunsAnywhereAction("b")))
    assert ctx.attrs["a"] == caller
    assert ctx.attrs["b"] == caller


def test_async_only_tree_is_refused_by_sync_run() -> None:
    # "has_async_only_atom -> needs loop": sync run must refuse and point to arun.
    with pytest.raises(RuntimeError):
        run(Sequential(AsyncOnlyAction("a")))


async def test_async_only_tree_runs_under_arun() -> None:
    loop = _this_thread()
    _, ctx = await arun(Sequential(AsyncOnlyAction("a")))
    assert ctx.attrs["a"] == loop


# --- pure compute, parallel (doc: "Add | Add" -> threads) -----------------


def test_pure_parallel_dispatches_to_threads() -> None:
    # No async-only -> on_loop=false; each runs-anywhere child inherits false
    # and dispatches to a worker thread.
    _, ctx = run(Parallel(RunsAnywhereAction("a"), RunsAnywhereAction("b")), max_parallel=2)
    assert _is_worker(ctx.attrs["a"])
    assert _is_worker(ctx.attrs["b"])


# --- async I/O, parallel (doc: "HttpFetch | HttpFetch" -> gather) ---------


async def test_async_parallel_runs_every_child_on_the_loop() -> None:
    loop = _this_thread()
    _, ctx = await arun(Parallel(AsyncOnlyAction("a"), AsyncOnlyAction("b")), max_parallel=2)
    assert ctx.attrs["a"] == loop
    assert ctx.attrs["b"] == loop


# --- mixed work, parallel, hybrid (doc: "HttpFetch | sum(big_array)") -----


async def test_hybrid_parallel_splits_loop_and_thread() -> None:
    # async-only child -> on_loop=true (loop); sync-only child -> on_loop=false
    # (thread). One parallel node coordinates both.
    loop = _this_thread()
    _, ctx = await arun(Parallel(AsyncOnlyAction("io"), SyncOnlyAction("cpu")), max_parallel=2)
    assert ctx.attrs["io"] == loop
    assert _is_worker(ctx.attrs["cpu"])


# --- runs-anywhere child in a loop tree (doc: "Sleep | HttpFetch") --------


async def test_runs_anywhere_child_inherits_loop_under_async_parallel() -> None:
    # The runs-anywhere child holds no async-only atom, so its placement is
    # decided by the parent: a loop is already live -> it inherits on_loop=true
    # and runs on the loop, not a thread.
    loop = _this_thread()
    _, ctx = await arun(Parallel(AsyncOnlyAction("io"), RunsAnywhereAction("any")), max_parallel=2)
    assert ctx.attrs["io"] == loop
    assert ctx.attrs["any"] == loop


# --- sequential containing parallel (doc: "HttpFetch >> (C1 | C2)") --------


async def test_sequential_containing_parallel_places_each_branch() -> None:
    # Outer >> threads on_loop=true to both children. The async-only first child
    # runs on the loop; the inner parallel's sync-only children offload to
    # worker threads.
    loop = _this_thread()
    tree = Sequential(
        AsyncOnlyAction("first"),
        Parallel(SyncOnlyAction("p1"), SyncOnlyAction("p2")),
    )
    _, ctx = await arun(tree, max_parallel=2)
    assert ctx.attrs["first"] == loop
    assert _is_worker(ctx.attrs["p1"])
    assert _is_worker(ctx.attrs["p2"])


# --- the Budget gate: max_parallel == 1 sequentializes --------------------


def test_parallel_falls_through_to_sequential_at_max_parallel_one() -> None:
    # No pool allocated -> the parallel join runs each child inline on the
    # caller thread rather than on workers.
    caller = _this_thread()
    _, ctx = run(Parallel(RunsAnywhereAction("a"), RunsAnywhereAction("b")))
    assert ctx.attrs["a"] == caller
    assert ctx.attrs["b"] == caller
