"""End-to-end placement tests for Parallel / Race / AnyN across tree shapes.

Complements ``test_eval_modes_e2e.py`` by pinning per-child placement in the
shapes the taxonomy relocation and Dyn work will need to preserve: pure and
mixed Parallel, nested Parallel, Parallel under a Span, Race and AnyN over
mixed children, Race / AnyN nested and mixed with Parallel, and Parallel
cancellation on a child error.

Placement is observed the same way as ``test_eval_modes_e2e.py``: each async
atom records ``threading.current_thread().name``; ``AsyncOnlyAction`` /
``SyncOnlyAction`` raise on their wrong path so misplacement fails loudly.
"""

from __future__ import annotations

import threading

import pytest
from _support.async_atoms import (
    AsyncOnlyAction,
    BoomAction,
    SleepAndRecordAction,
    SyncOnlyAction,
)
from _support.passthrough_span import PassBracket

from nu.flows import AnyN, Parallel, Race
from nu.lang.helpers import arun


def _this_thread() -> str:
    return threading.current_thread().name


def _is_worker(name: str) -> bool:
    return name.startswith("nu-worker")


# --- Parallel: uniform-child shapes --------------------------------------


async def test_parallel_two_async_only_children_both_on_loop() -> None:
    loop = _this_thread()
    _, ctx = await arun(
        Parallel(AsyncOnlyAction("a"), AsyncOnlyAction("b")),
        max_parallel=2,
    )
    assert ctx.attrs["a"] == loop
    assert ctx.attrs["b"] == loop


async def test_parallel_two_sync_only_children_both_off_loop() -> None:
    _, ctx = await arun(
        Parallel(SyncOnlyAction("a"), SyncOnlyAction("b")),
        max_parallel=2,
    )
    assert _is_worker(ctx.attrs["a"])
    assert _is_worker(ctx.attrs["b"])


# --- Parallel: nesting ---------------------------------------------------


async def test_nested_parallel_places_each_inner_child_correctly() -> None:
    loop = _this_thread()
    tree = Parallel(
        Parallel(AsyncOnlyAction("a"), SyncOnlyAction("b")),
        Parallel(AsyncOnlyAction("c"), SyncOnlyAction("d")),
    )
    _, ctx = await arun(tree, max_parallel=4)
    assert ctx.attrs["a"] == loop
    assert _is_worker(ctx.attrs["b"])
    assert ctx.attrs["c"] == loop
    assert _is_worker(ctx.attrs["d"])


# --- Parallel: under a Span transparency ---------------------------------


async def test_parallel_under_span_preserves_per_child_placement() -> None:
    # A passthrough Bracket wrapping each child must not perturb the child's
    # scheduling classification: the async-only body still runs on the loop,
    # the sync-only body still offloads to a worker thread.
    loop = _this_thread()
    tree = Parallel(
        PassBracket(AsyncOnlyAction("io")),
        PassBracket(SyncOnlyAction("cpu")),
    )
    _, ctx = await arun(tree, max_parallel=2)
    assert ctx.attrs["io"] == loop
    assert _is_worker(ctx.attrs["cpu"])


# --- Race: uniform and mixed children ------------------------------------


async def test_race_two_async_only_children_run_on_loop() -> None:
    # Both children complete fast (asyncio.sleep(0)); whichever the wait picks
    # first, the recorded thread must be the loop for whichever ran.
    loop = _this_thread()
    _, ctx = await arun(
        Race(AsyncOnlyAction("a"), AsyncOnlyAction("b")),
        max_parallel=2,
    )
    ran = [(k, v) for k, v in ctx.attrs.items() if k in {"a", "b"}]
    assert ran, "expected at least one Race child to have recorded"
    for _, thread in ran:
        assert thread == loop


async def test_race_mixed_async_and_sync_child_place_correctly() -> None:
    # Race under async runtime with max_parallel>1 uses _drive_async, so the
    # sync-only child offloads to a worker while the async-only child stays on
    # the loop. Whichever wins first, the recorded thread must match its class.
    loop = _this_thread()
    _, ctx = await arun(
        Race(AsyncOnlyAction("io"), SyncOnlyAction("cpu")),
        max_parallel=2,
    )
    if "io" in ctx.attrs:
        assert ctx.attrs["io"] == loop
    if "cpu" in ctx.attrs:
        assert _is_worker(ctx.attrs["cpu"])
    assert "io" in ctx.attrs or "cpu" in ctx.attrs


async def test_nested_race_places_children_independently_of_outer() -> None:
    loop = _this_thread()
    _, ctx = await arun(
        Race(
            Race(AsyncOnlyAction("a"), AsyncOnlyAction("b")),
            AsyncOnlyAction("c"),
        ),
        max_parallel=3,
    )
    ran = [(k, v) for k, v in ctx.attrs.items() if k in {"a", "b", "c"}]
    assert ran
    for _, thread in ran:
        assert thread == loop


async def test_race_under_parallel_places_children_correctly() -> None:
    # Parallel(Race(A,B), Race(C,D)) - inner Races each pick a winner; the
    # outer Parallel joins them. Recorded threads for whichever ran match the
    # child's class.
    loop = _this_thread()
    tree = Parallel(
        Race(AsyncOnlyAction("a"), AsyncOnlyAction("b")),
        Race(AsyncOnlyAction("c"), AsyncOnlyAction("d")),
    )
    _, ctx = await arun(tree, max_parallel=4)
    ran = [(k, v) for k, v in ctx.attrs.items() if k in {"a", "b", "c", "d"}]
    assert ran
    for _, thread in ran:
        assert thread == loop


# --- AnyN: uniform, mixed, nested ---------------------------------------


async def test_any_two_async_only_children_run_on_loop() -> None:
    loop = _this_thread()
    _, ctx = await arun(
        AnyN(AsyncOnlyAction("a"), AsyncOnlyAction("b")),
        max_parallel=2,
    )
    ran = [(k, v) for k, v in ctx.attrs.items() if k in {"a", "b"}]
    assert ran
    for _, thread in ran:
        assert thread == loop


async def test_any_mixed_async_and_sync_child_place_correctly() -> None:
    loop = _this_thread()
    _, ctx = await arun(
        AnyN(AsyncOnlyAction("io"), SyncOnlyAction("cpu")),
        max_parallel=2,
    )
    if "io" in ctx.attrs:
        assert ctx.attrs["io"] == loop
    if "cpu" in ctx.attrs:
        assert _is_worker(ctx.attrs["cpu"])
    assert "io" in ctx.attrs or "cpu" in ctx.attrs


async def test_nested_any_places_children_independently_of_outer() -> None:
    loop = _this_thread()
    _, ctx = await arun(
        AnyN(
            AnyN(AsyncOnlyAction("a"), AsyncOnlyAction("b")),
            AsyncOnlyAction("c"),
        ),
        max_parallel=3,
    )
    ran = [(k, v) for k, v in ctx.attrs.items() if k in {"a", "b", "c"}]
    assert ran
    for _, thread in ran:
        assert thread == loop


async def test_any_under_parallel_places_children_correctly() -> None:
    loop = _this_thread()
    tree = Parallel(
        AnyN(AsyncOnlyAction("a"), AsyncOnlyAction("b")),
        AnyN(AsyncOnlyAction("c"), AsyncOnlyAction("d")),
    )
    _, ctx = await arun(tree, max_parallel=4)
    ran = [(k, v) for k, v in ctx.attrs.items() if k in {"a", "b", "c", "d"}]
    assert ran
    for _, thread in ran:
        assert thread == loop


# --- Parallel: cancellation on child error --------------------------------


async def test_parallel_cancels_slow_sibling_when_a_child_raises() -> None:
    # asyncio.gather propagates the first exception and cancels the rest.
    # The sleep-and-record sibling should be cancelled during its sleep so its
    # name never lands in ctx.attrs, and the ValueError from BoomAction surfaces.
    tree = Parallel(BoomAction("bad"), SleepAndRecordAction("slow", delay=0.5))
    with pytest.raises(ValueError, match="bad"):
        await arun(tree, max_parallel=2)


async def test_parallel_error_surfaces_and_sibling_wrote_nothing() -> None:
    # Separate assertion: verify the sibling side of the cancellation.
    # A fresh context, drive again, then inspect - we only get ctx back on
    # success, so use a Sequential wrapper that swallows via ExceptionGroup?
    # Simpler: rely on a mutable capture list in the sibling to prove it never
    # completed.
    captured: list[str] = []

    from nu.engine.structure import Declared
    from nu.lang import ScalarAction

    class RecordOnCompleteAction(ScalarAction):
        _requires_async = Declared(value=True, name="requires_async")
        _mutates = Declared(value=frozenset({0}), name="mutates")

        def __init__(self, name: str) -> None:
            super().__init__()
            self._payload["name"] = name

        def _compile(self, nid, children):
            def thunk(rt):
                msg = "sync path not expected"
                raise RuntimeError(msg)

            return thunk

        def _acompile(self, nid, children):
            name = self._payload["name"]

            async def athunk(rt):
                import asyncio

                await asyncio.sleep(0.5)
                captured.append(name)
                return name

            return athunk

    tree = Parallel(BoomAction("bad"), RecordOnCompleteAction("slow"))
    with pytest.raises(ValueError, match="bad"):
        await arun(tree, max_parallel=2)
    assert captured == [], f"sibling should have been cancelled, got {captured}"
