"""``nu.mem.Frame``: a private mem store for one scope.

The frame's promises, one test group each: what the body sees on entry, what
``initial`` writes, what it yields, that the binding ends with the body however
the body ends, that every run gets its own dict, and the two errors it raises.
Every behavioral test runs under both runners.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
import nu.mem as nm
from nu.lang import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable


class S(nu.Shape):
    a = nm.IntRef.slot()
    b = nm.IntRef.slot()


class T(nu.Shape):
    c = nm.IntRef.slot()


class Out(nu.Shape):
    """A dict the test binds itself, to see what ran inside frames."""

    log = nm.ListRef.slot(int)
    first = nm.IntRef.slot()
    second = nm.IntRef.slot()


CALLS: list[int] = []


class Counted(nu.ScalarQuery):
    """Yields 5 and records every evaluation, so a test can count them."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: object) -> int:
            CALLS.append(1)
            return 5

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: object) -> int:
            CALLS.append(1)
            return 5

        return athunk


def _sync(term: nu.Nu, ctx: nu.Context | None = None) -> object:
    return nu.run(term, ctx)[0]


def _async(term: nu.Nu, ctx: nu.Context | None = None) -> object:
    return asyncio.run(nu.arun(term, ctx))[0]


RUNNERS = pytest.mark.parametrize("run", [_sync, _async], ids=["sync", "async"])


def _out() -> tuple[dict, nu.Context]:
    data: dict = {"log": []}
    return data, nu.Context().bind(dict, data, Out)


# --- entry and initial ---------------------------------------------------------


@RUNNERS
def test_the_body_starts_on_an_empty_store(run: Callable) -> None:
    assert run(nm.Frame(S, S.a)) is EMPTY


@RUNNERS
def test_initial_values_land_in_their_slots(run: Callable) -> None:
    assert run(nm.Frame(S, S.a + S.b, a=1, b=nu.Add(1, 1))) == 3


@RUNNERS
def test_initial_values_are_written_in_keyword_order(run: Callable) -> None:
    assert run(nm.Frame(S, S.b, a=1, b=S.a + 10)) == 11


@RUNNERS
def test_an_initial_term_is_evaluated_once(run: Callable) -> None:
    CALLS.clear()
    assert run(nm.Frame(S, S.a + S.a, a=Counted())) == 10
    assert len(CALLS) == 1


@RUNNERS
def test_the_body_writes_and_reads_the_frame(run: Callable) -> None:
    loop = nu.ForEachDo(nu.Iter([1, 2, 3]), S.a.set(S.a + nu.context.Attr("item")))
    data, ctx = _out()
    run(nm.Frame(S, loop >> Out.first.set(S.a), a=0), ctx)
    assert data["first"] == 6


# --- yields --------------------------------------------------------------------


@RUNNERS
def test_a_scalar_body_yields_through(run: Callable) -> None:
    assert run(nm.Frame(S, nu.Add(S.a, 1), a=41)) == 42


@RUNNERS
def test_a_stream_body_reads_the_frame_across_its_drain(run: Callable) -> None:
    stream = nu.Map(nu.Iter([1, 2]), S.a + nu.context.Attr("item"))
    assert run(nu.Collect(nm.Frame(S, stream, a=10))) == [11, 12]


def test_a_stream_body_stays_a_stream() -> None:
    stream = nm.Frame(S, nu.Map(nu.Iter([1, 2]), S.a + nu.context.Attr("item")), a=10)
    assert list(nu.run(stream)[0]) == [11, 12]


# --- exit ----------------------------------------------------------------------


@RUNNERS
def test_the_binding_ends_with_the_body(run: Callable) -> None:
    ctx = nu.Context()
    run(nm.Frame(S, S.a, a=1), ctx)
    assert not ctx.fabrics.has(dict, S)


@RUNNERS
def test_the_binding_ends_when_the_body_raises(run: Callable) -> None:
    ctx = nu.Context()
    with pytest.raises(ValueError, match="boom"):
        run(nm.Frame(S, nu.raise_(ValueError, "boom"), a=1), ctx)
    assert not ctx.fabrics.has(dict, S)


@RUNNERS
def test_an_error_inside_restores_the_outer_frame(run: Callable) -> None:
    inner = nu.TryCatch(nm.Frame(S, nu.raise_(ValueError, "boom"), a=2), catch=Out.second.set(0))
    data, ctx = _out()
    run(nm.Frame(S, inner >> Out.first.set(S.a), a=1), ctx)
    assert (data["first"], data["second"]) == (1, 0)


def test_the_binding_ends_when_the_body_is_cancelled() -> None:
    ctx = nu.Context()

    async def go() -> None:
        task = asyncio.ensure_future(nu.arun(nm.Frame(S, nu.Delay(10.0), a=1), ctx))
        await asyncio.sleep(0.05)
        assert ctx.fabrics.has(dict, S)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(go())
    assert not ctx.fabrics.has(dict, S)


def test_a_stream_body_releases_the_frame_once_drained() -> None:
    ctx = nu.Context()
    stream = nu.run(nm.Frame(S, nu.Map(nu.Iter([1, 2]), S.a + nu.context.Attr("item")), a=10), ctx)[
        0
    ]
    first = next(iter(stream))
    assert first == 11
    assert ctx.fabrics.has(dict, S)
    assert list(stream) == [12]
    assert not ctx.fabrics.has(dict, S)


# --- isolation -----------------------------------------------------------------


@RUNNERS
def test_same_shape_nested_shadows_then_restores(run: Callable) -> None:
    data, ctx = _out()
    inner = nm.Frame(S, Out.first.set(S.a), a=2)
    run(nm.Frame(S, inner >> Out.second.set(S.a), a=1), ctx)
    assert (data["first"], data["second"]) == (2, 1)


@RUNNERS
def test_different_shapes_coexist(run: Callable) -> None:
    assert run(nm.Frame(S, nm.Frame(T, S.a + T.c, c=2), a=1)) == 3


@RUNNERS
def test_every_run_gets_its_own_dict(run: Callable) -> None:
    data, ctx = _out()
    frame = nm.Frame(S, S.a.init(nu.context.Attr("item")) >> Out.log.append(S.a))
    run(nu.ForEachDo(nu.Iter([1, 2, 3]), frame), ctx)
    assert data["log"] == [1, 2, 3]


@RUNNERS
def test_parallel_arms_entering_a_frame_are_isolated(run: Callable) -> None:
    data, ctx = _out()
    arms = nu.Parallel(
        nm.Frame(S, S.a.set(S.a + 1) >> Out.first.set(S.a), a=0),
        nm.Frame(S, S.a.set(S.a + 1) >> Out.second.set(S.a), a=10),
    )
    run(arms, ctx)
    assert (data["first"], data["second"]) == (1, 11)


def test_concurrent_frames_never_see_each_other() -> None:
    data, ctx = _out()
    arms = nu.Parallel(
        nm.Frame(S, nu.DelayedDo(0.05, Out.first.set(S.a)), a=1),
        nm.Frame(S, nu.DelayedDo(0.01, S.a.set(3)) >> Out.second.set(S.a), a=2),
    )
    asyncio.run(nu.arun(arms, ctx))
    assert (data["first"], data["second"]) == (1, 3)


@RUNNERS
def test_arms_inside_one_frame_share_it(run: Callable) -> None:
    arms = nu.Parallel(S.a.set(1), S.b.set(2))
    data, ctx = _out()
    run(nm.Frame(S, arms >> Out.first.set(S.a + S.b)), ctx)
    assert data["first"] == 3


# --- errors --------------------------------------------------------------------


@RUNNERS
def test_reading_a_shape_with_no_frame_names_the_shape(run: Callable) -> None:
    with pytest.raises(LookupError, match=r"dict\[S\]"):
        run(S.a)


def test_an_unknown_initial_key_raises_at_construction() -> None:
    with pytest.raises(TypeError, match=r"\['z'\] are not slots of S"):
        nm.Frame(S, S.a, z=1)


@RUNNERS
def test_a_sentinel_initial_value_raises_on_entry(run: Callable) -> None:
    with pytest.raises(ValueError, match="sentinel"):
        run(nm.Frame(S, S.a, a=nu.context.Attr("missing")))
