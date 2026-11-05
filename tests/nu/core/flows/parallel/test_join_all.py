"""Parallel joins on every branch: nothing is left running when it returns.

A cancel of the caller, or one branch raising, ends the join only once every
branch has finished unwinding. Pinned here for both the plain on-loop path
(``max_parallel=1``) and the placement-aware one, for ``Parallel`` and
``ParallelAsync``, and for ``ForEachParAsync`` which joins the same way:

- a cancel returns only after a slow-to-unwind branch has drained, and each
  branch's cleanup runs to its end instead of being cancelled a second time;
- an error cancels the siblings and drains them before it surfaces;
- a reactive branch has unbound and closed its subscription by the time the
  cancelled parallel returns;
- values still come back in child order, and the error that tripped the
  join is the one that surfaces.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from _support.reactive import QUIET, Body, Feed, start, until

from nu.context import Attr
from nu.core import Iter
from nu.core.flows import Parallel, ParallelAsync
from nu.core.flows.control import ForEachParAsync
from nu.core.flows.parallel._scheduling import _join_all
from nu.core.reactive import ReactEvery, Reconcile
from nu.core.reactive.level import ReconcileLatestEach
from nu.lang import Context, Literal
from nu.lang.helpers import arun


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


KINDS = [Parallel, ParallelAsync]
WIDTHS = [1, 2]


def _slow_unwind(log: list, name: str, unwind: float) -> Body:
    """A branch that parks forever and takes ``unwind`` seconds to clean up."""

    async def fn(rt: Runtime) -> None:
        log.append(f"{name} start")
        try:
            await asyncio.Event().wait()
        finally:
            try:
                await asyncio.sleep(unwind)
                log.append(f"{name} unwound")
            except asyncio.CancelledError:
                log.append(f"{name} cleanup cut")
                raise

    return Body(fn)


async def _forever(rt: Runtime) -> None:
    await asyncio.Event().wait()


async def _cancel_once(task: asyncio.Task) -> None:
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("kind", KINDS)
async def test_cancel_returns_only_after_every_branch_unwound(kind: type, width: int) -> None:
    log: list = []
    # Two branches: at width 2 the budget admits no more than that at once.
    term = kind(_slow_unwind(log, "a", 0.03), _slow_unwind(log, "b", 0.08))
    task = asyncio.ensure_future(arun(term, max_parallel=width))
    await until(lambda: len(log) == 2)
    await _cancel_once(task)
    assert sorted(log[2:]) == ["a unwound", "b unwound"]


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("kind", KINDS)
async def test_error_cancels_and_drains_the_siblings(kind: type, width: int) -> None:
    log: list = []

    async def boom(rt: Runtime) -> None:
        await until(lambda: "a start" in log)
        msg = "boom"
        raise RuntimeError(msg)

    term = kind(_slow_unwind(log, "a", 0.05), Body(boom))
    with pytest.raises(RuntimeError, match="boom"):
        await arun(term, max_parallel=width)
    assert log == ["a start", "a unwound"]


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("kind", KINDS)
async def test_reactive_branch_unbound_and_closed_when_cancel_returns(
    kind: type, width: int
) -> None:
    log: list = []
    feed = Feed()
    each = ReconcileLatestEach(Iter(["a"]), Attr("feed"), _slow_unwind(log, "arm", 0.05), **QUIET)
    task = asyncio.ensure_future(
        arun(kind(each, Body(_forever)), Context(attrs={"feed": feed}), max_parallel=width)
    )
    await until(lambda: "arm start" in log)
    await _cancel_once(task)
    assert log == ["arm start", "arm unwound"]
    assert feed.log == ["bind", "unbind", "close"]
    assert feed.receivers == []


class _Unbindable(Feed):
    """A subscription that cannot be bound, like a session double with no ``subscribe``."""

    def bind(self, receiver: object) -> None:
        msg = "no subscribe"
        raise AttributeError(msg)


@pytest.mark.parametrize("width", WIDTHS)
async def test_a_failed_react_takes_its_live_reconcile_sibling_down(width: int) -> None:
    # A viewer's shape: a ReactEvery on one change next to a Reconcile on
    # another. The ReactEvery fails at bind, so the parallel fails, and the
    # Reconcile must not keep running and answering changes headless after
    # the caller has its error.
    drawn: list = []
    feed = Feed()

    async def draw(rt: Runtime) -> None:
        drawn.append(len(drawn))

    term = ParallelAsync(
        ReactEvery(Attr("dead"), Body(_forever)),
        Reconcile(Attr("feed"), Body(draw), **QUIET),
    )
    attrs = {"dead": _Unbindable(), "feed": feed}
    with pytest.raises(AttributeError, match="no subscribe"):
        await arun(term, Context(attrs=attrs), max_parallel=width)
    assert feed.receivers == []
    before = list(drawn)
    feed.fire()
    await asyncio.sleep(0.05)
    assert drawn == before


async def test_join_all_keeps_child_order() -> None:
    # Parallel is a strategy over actions, so the order is pinned on the join.
    async def after(delay: float, value: str) -> str:
        await asyncio.sleep(delay)
        return value

    tasks = [asyncio.ensure_future(after(d, v)) for d, v in ((0.03, "a"), (0.0, "b"), (0.01, "c"))]
    assert await _join_all(tasks) == ["a", "b", "c"]


async def test_join_all_raises_the_error_that_tripped_it() -> None:
    # A sibling that raises while being cancelled does not mask the first error.
    async def first() -> None:
        msg = "first"
        raise RuntimeError(msg)

    async def noisy() -> None:
        try:
            await asyncio.Event().wait()
        finally:
            msg = "while cancelled"
            raise ValueError(msg)

    with pytest.raises(RuntimeError, match="first"):
        await _join_all([asyncio.ensure_future(noisy()), asyncio.ensure_future(first())])


async def test_join_all_of_nothing_is_empty() -> None:
    assert await _join_all([]) == []


async def test_foreach_par_cancel_lets_every_arm_finish_its_cleanup() -> None:
    log: list = []

    async def arm(rt: Runtime) -> None:
        name = rt.ctx.attrs.get("item")
        await _slow_unwind(log, name, {"a": 0.0, "b": 0.05, "c": 0.1}[name])._payload["fn"](rt)

    task = start(ForEachParAsync(Iter(Literal(["a", "b", "c"])), Body(arm)))
    await until(lambda: len(log) == 3)
    await _cancel_once(task)
    assert sorted(log[3:]) == ["a unwound", "b unwound", "c unwound"]
