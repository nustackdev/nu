"""Tests for ForEachParAsync - the fan-out ForEach, loop only.

One arm per element of a runtime list, all on the loop at once, joining on
all. What is pinned here: the arms genuinely overlap (they cannot finish
otherwise), each arm reads its own element and never a sibling's, arms that
never return are fine, cancellation reaches every arm through ``Race``, an
empty list returns straight away, a raising arm surfaces instead of vanishing,
and a sync ``run`` is refused rather than degraded.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
from nu.core import Iter
from nu.core.flows import ForeverDo, Race
from nu.core.flows.control import ForEachParAsync
from nu.domains.shape.interactions import SetCmd
from nu.engine.structure import Declared
from nu.lang import Attr, Context, Control, Literal, Ref, ScalarAction
from nu.lang.attributes.execution import ExecOrder
from nu.lang.helpers import arun, compile, run


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


# --- arm atoms ------------------------------------------------------------


class ArmAsync(ScalarAction):
    """Async-only arm running ``fn(item)``; the body every async test drives.

    ``item`` is the child the arm reads its element through, the ref its
    lambda is handed; ``fn`` gets an async reader of it, so a test can read
    the element again after an await.
    """

    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fn: Callable, item: object = None) -> None:
        super().__init__(item)
        self._fn = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "ArmAsync was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._fn
        (item_t,) = children

        async def athunk(rt: Runtime) -> object:
            return await fn(lambda: item_t(rt))

        return athunk


def _items(*values: object) -> Iter:
    return Iter(Literal(list(values)))


def _write() -> SetCmd:
    """A plain Command body, for the tests that only compile or refuse the tree."""
    return SetCmd(Ref("a"), Literal(1))


def _arm(fn: Callable) -> Callable:
    """The lambda body over the element, an ``ArmAsync`` reading it."""
    return lambda item: ArmAsync(fn, item)


class Shared(nu.Shape):
    """A dict bound above the fan-out, seen by every arm."""

    log = nu.ListRef.slot(int)


# --- basis ----------------------------------------------------------------


def test_foreach_par_async_is_a_control() -> None:
    assert issubclass(ForEachParAsync, Control)


def test_foreach_par_async_param_slots_mark_the_items() -> None:
    program = compile(ForEachParAsync(_items(1), _write()))
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset({0})


def test_foreach_par_async_declares_parallel_exec_order() -> None:
    program = compile(ForEachParAsync(_items(1), _write()))
    assert program.attr(program.root, Attr.EXEC_ORDER) is ExecOrder.PARALLEL


# --- concurrency is real --------------------------------------------------


async def test_arms_overlap_rather_than_run_in_sequence() -> None:
    # Every arm parks until all three have arrived. Sequential arms would
    # deadlock on the first one, so finishing at all proves the overlap.
    everyone_here = asyncio.Event()
    arrived: list[object] = []

    async def arm(item: Callable) -> None:
        arrived.append(await item())
        if len(arrived) == 3:
            everyone_here.set()
        await asyncio.wait_for(everyone_here.wait(), timeout=2)

    await arun(ForEachParAsync(_items("a", "b", "c"), _arm(arm)))
    assert sorted(arrived) == ["a", "b", "c"]


# --- per-arm item isolation ----------------------------------------------


async def test_each_arm_keeps_its_own_item_across_awaits() -> None:
    # The arms interleave on purpose: a shared frame would leave every arm
    # reading whichever element was written last.
    seen: list[tuple[object, object]] = []

    async def arm(item: Callable) -> None:
        mine = await item()
        for _ in range(3):
            await asyncio.sleep(0.01)
            seen.append((mine, await item()))

    await arun(ForEachParAsync(_items(1, 2, 3), _arm(arm)))
    assert len(seen) == 9
    assert all(mine == now for mine, now in seen)
    assert sorted({mine for mine, _ in seen}) == [1, 2, 3]


async def test_arm_frames_stay_in_the_arm_and_values_stay_shared() -> None:
    # Own frames: an arm's frame never reaches the caller. Shared values: the
    # dict bound above the fan-out is the same object in every arm.
    data: dict = {"log": []}
    ctx = Context().bind(dict, data, Shared)
    term = ForEachParAsync(_items(1, 2), lambda item: Shared.log.append(item))
    _, out = await arun(term, ctx)
    assert out is ctx
    assert sorted(data["log"]) == [1, 2]
    assert data == {"log": data["log"]}


# --- never-returning arms + cancellation ---------------------------------


async def test_never_returning_arms_are_cancelled_through_race() -> None:
    started: list[object] = []
    cancelled: list[object] = []
    done: list[bool] = []

    async def arm(item: Callable) -> None:
        started.append(await item())
        try:
            await asyncio.Event().wait()  # never returns on its own
        except asyncio.CancelledError:
            cancelled.append(await item())
            raise

    async def finisher(item: Callable) -> None:
        while len(started) < 3:
            await asyncio.sleep(0.01)
        done.append(True)

    await arun(
        Race(
            ForEachParAsync(_items(1, 2, 3), lambda item: ForeverDo(ArmAsync(arm, item))),
            ArmAsync(finisher),
        )
    )
    assert done == [True]
    assert sorted(started) == [1, 2, 3]
    assert sorted(cancelled) == [1, 2, 3]


# --- empty list -----------------------------------------------------------


async def test_empty_items_completes_immediately() -> None:
    ran: list[object] = []

    async def arm(item: Callable) -> None:
        ran.append(await item())

    await asyncio.wait_for(
        arun(ForEachParAsync(_items(), _arm(arm))),
        timeout=2,
    )
    assert ran == []


# --- a failing arm --------------------------------------------------------


async def test_a_raising_arm_surfaces_and_the_others_are_cancelled() -> None:
    cancelled: list[object] = []

    async def arm(item: Callable) -> None:
        if await item() == "boom":
            raise ValueError("boom")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.append(await item())
            raise

    with pytest.raises(ValueError, match="boom"):
        await arun(ForEachParAsync(_items("a", "boom", "b"), _arm(arm)))
    assert sorted(cancelled) == ["a", "b"]


# --- sync entry points are refused ----------------------------------------


def test_sync_run_is_refused_and_the_message_names_the_atom() -> None:
    # The body here is runs-anywhere, so the atom is the only thing forcing
    # the loop and the refusal has to point at it by name.
    with pytest.raises(RuntimeError, match=r"async-only atom \(ForEachParAsync\); use aeval"):
        run(ForEachParAsync(_items(1), _write()))


def test_the_sync_thunk_names_the_atom_and_points_at_arun() -> None:
    program = compile(ForEachParAsync(_items(1), _write()))
    with pytest.raises(RuntimeError, match="ForEachParAsync requires an async runtime; use arun"):
        program.thunks[program.id_of[program.root]](None)


def test_foreach_par_async_requires_async() -> None:
    program = compile(ForEachParAsync(_items(1), _write()))
    assert program.attr(program.root, Attr.REQUIRES_ASYNC) is True
