"""Tests for ForEachParAsync - the fan-out ForEach, loop only.

One arm per element of a runtime list, all on the loop at once, joining on
all. What is pinned here: the arms genuinely overlap (they cannot finish
otherwise), each arm sees its own ``item`` and never a sibling's, arms that
never return are fine, cancellation reaches every arm through ``Race``, an
empty list returns straight away, a raising arm surfaces instead of vanishing,
and a sync ``run`` is refused rather than degraded.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from nu.context import AttrRef, SetCmd
from nu.core import Iter
from nu.core.flows import ForeverDo, Race
from nu.core.flows.control import ForEachParAsync
from nu.engine.structure import Declared
from nu.lang import Attr, Context, Control, Literal, ScalarAction
from nu.lang.attributes.execution import ExecOrder
from nu.lang.helpers import arun, compile, run


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Attributes, Runtime


# --- arm atoms ------------------------------------------------------------


class ArmAsync(ScalarAction):
    """Async-only arm running ``fn(attrs)``; the body every async test drives."""

    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fn: Callable) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "ArmAsync was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return await fn(rt.ctx.attrs)

        return athunk


def _items(*values: object) -> Iter:
    return Iter(Literal(list(values)))


def _seed(**attrs: object) -> Context:
    ctx = Context()
    for key, value in attrs.items():
        ctx.attrs[key] = value
    return ctx


# --- basis ----------------------------------------------------------------


def test_foreach_par_async_is_a_control() -> None:
    assert issubclass(ForEachParAsync, Control)


def test_foreach_par_async_param_slots_mark_items_and_the_name() -> None:
    program = compile(ForEachParAsync(_items(1), SetCmd(AttrRef("a"), Literal(1))))
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset({0, 2})


def test_foreach_par_async_declares_parallel_exec_order() -> None:
    program = compile(ForEachParAsync(_items(1), SetCmd(AttrRef("a"), Literal(1))))
    assert program.attr(program.root, Attr.EXEC_ORDER) is ExecOrder.PARALLEL


# --- concurrency is real --------------------------------------------------


async def test_arms_overlap_rather_than_run_in_sequence() -> None:
    # Every arm parks until all three have arrived. Sequential arms would
    # deadlock on the first one, so finishing at all proves the overlap.
    everyone_here = asyncio.Event()
    arrived: list[object] = []

    async def arm(attrs: Attributes) -> None:
        arrived.append(attrs["item"])
        if len(arrived) == 3:
            everyone_here.set()
        await asyncio.wait_for(everyone_here.wait(), timeout=2)

    await arun(ForEachParAsync(_items("a", "b", "c"), ArmAsync(arm)))
    assert sorted(arrived) == ["a", "b", "c"]


# --- per-arm item isolation ----------------------------------------------


async def test_each_arm_keeps_its_own_item_across_awaits() -> None:
    # The arms interleave on purpose: a shared attrs store would leave every
    # arm reading whichever element was bound last.
    seen: list[tuple[object, object]] = []

    async def arm(attrs: Attributes) -> None:
        mine = attrs["item"]
        for _ in range(3):
            await asyncio.sleep(0.01)
            seen.append((mine, attrs["item"]))

    await arun(ForEachParAsync(_items(1, 2, 3), ArmAsync(arm)))
    assert len(seen) == 9
    assert all(mine == now for mine, now in seen)
    assert sorted({mine for mine, _ in seen}) == [1, 2, 3]


async def test_arm_writes_stay_in_the_arm_and_values_stay_shared() -> None:
    # Own key space: the arm's own binding never reaches the caller. Shared
    # values: the list the caller put in attrs is the same object in the arm.
    log: list[object] = []

    async def arm(attrs: Attributes) -> None:
        attrs["mine"] = attrs["item"]
        attrs["log"].append(attrs["item"])

    _, ctx = await arun(ForEachParAsync(_items(1, 2), ArmAsync(arm)), _seed(log=log))
    assert "mine" not in ctx.attrs
    assert sorted(ctx.attrs["log"]) == [1, 2]
    assert ctx.attrs["log"] is log


# --- never-returning arms + cancellation ---------------------------------


async def test_never_returning_arms_are_cancelled_through_race() -> None:
    started: list[object] = []
    cancelled: list[object] = []

    async def arm(attrs: Attributes) -> None:
        started.append(attrs["item"])
        try:
            await asyncio.Event().wait()  # never returns on its own
        except asyncio.CancelledError:
            cancelled.append(attrs["item"])
            raise

    async def finisher(attrs: Attributes) -> None:
        while len(started) < 3:
            await asyncio.sleep(0.01)
        attrs["done"] = True

    _, ctx = await arun(
        Race(
            ForEachParAsync(_items(1, 2, 3), ForeverDo(ArmAsync(arm))),
            ArmAsync(finisher),
        )
    )
    assert ctx.attrs["done"] is True
    assert sorted(started) == [1, 2, 3]
    assert sorted(cancelled) == [1, 2, 3]


# --- empty list -----------------------------------------------------------


async def test_empty_items_completes_immediately() -> None:
    ran: list[object] = []

    async def arm(attrs: Attributes) -> None:
        ran.append(attrs["item"])

    await asyncio.wait_for(
        arun(ForEachParAsync(_items(), ArmAsync(arm))),
        timeout=2,
    )
    assert ran == []


# --- a failing arm --------------------------------------------------------


async def test_a_raising_arm_surfaces_and_the_others_are_cancelled() -> None:
    cancelled: list[object] = []

    async def arm(attrs: Attributes) -> None:
        if attrs["item"] == "boom":
            raise ValueError("boom")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.append(attrs["item"])
            raise

    with pytest.raises(ValueError, match="boom"):
        await arun(ForEachParAsync(_items("a", "boom", "b"), ArmAsync(arm)))
    assert sorted(cancelled) == ["a", "b"]


# --- sync entry points are refused ----------------------------------------


def test_sync_run_is_refused_and_the_message_names_the_atom() -> None:
    # The body here is runs-anywhere, so the atom is the only thing forcing
    # the loop and the refusal has to point at it by name.
    with pytest.raises(RuntimeError, match=r"async-only atom \(ForEachParAsync\); use aeval"):
        run(ForEachParAsync(_items(1), SetCmd(AttrRef("a"), Literal(1))))


def test_the_sync_thunk_names_the_atom_and_points_at_arun() -> None:
    program = compile(ForEachParAsync(_items(1), SetCmd(AttrRef("a"), Literal(1))))
    with pytest.raises(RuntimeError, match="ForEachParAsync requires an async runtime; use arun"):
        program.thunks[program.id_of[program.root]](None)


def test_foreach_par_async_requires_async() -> None:
    program = compile(ForEachParAsync(_items(1), SetCmd(AttrRef("a"), Literal(1))))
    assert program.attr(program.root, Attr.REQUIRES_ASYNC) is True
