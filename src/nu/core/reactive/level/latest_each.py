"""ReconcileLatestEach: one arm per id read from state, kept live against a change.

``hold_arms`` is the engine: a level loop that reads the ids each wake and
aligns an ``ArmBook`` to them. ``ReconcileLatestEach`` runs it over a list of
ids, ``ReconcileLatest`` over one id or none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.core._stream import aiter_any
from nu.core.flows.parallel._scheduling import _spawn_arm
from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.attributes.execution import ExecOrder

from .._arms import ArmBook
from .._body import async_only
from ._wakes import Wakes, read_schedule, schedule_terms


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from nu.lang.runtime import Runtime

__all__ = ["ReconcileLatestEach", "hold_arms"]


async def hold_arms(
    owner: str,
    rt: Runtime,
    nid: int,
    children: tuple[Callable, ...],
    ids: Callable[[Runtime], Awaitable[Iterable]],
) -> None:
    """Keep one arm per id live against ``change``: the level loop behind the per-id flows.

    Args:
        owner: the flow's name, for error messages.
        rt: the runtime the flow runs under.
        nid: the flow's own node, whose third child is the body.
        children: the flow's compiled children ``(_, change, body, item,
            after, every)``; the first is read through ``ids`` instead.
        ids: answers the ids a pass should hold arms for.

    Notes:
        - One pass right after binding, one per notification, one per
          re-check, bursts merged. Each pass reads ``ids`` and aligns the
          arm book to the answer under its two rules: a finished arm is not
          started again while its id stays, and an arm error ends the flow.
        - Never returns on its own. On any exit the live arms are cancelled
          and drained first, then the subscription is unbound and closed,
          then the cancellation or error goes on.
    """
    _, change, _body, item, after, every = children
    name = await item(rt)
    schedule = await read_schedule(owner, rt, after, every)
    body_nid = rt.program.children[nid][2]
    book = ArmBook(lambda elem: _spawn_arm(rt, body_nid, elem, name), once=True, owner=owner)
    async with Wakes(await change(rt), *schedule) as wakes:
        try:
            while True:
                await book.wait(wakes.wait())
                await book.align(await ids(rt))
        finally:
            await book.drain()


class ReconcileLatestEach(Control):
    """``ReconcileLatestEach(items, change, lambda x: body)`` - one arm per element, kept live against ``change``.

    The level flow over a fan-out: each pass reads ``items`` and makes the
    arm set match it. Passes run right after subscribing, on every change,
    and on re-checks, with changes during a pass merged into one more.

    Args:
        items: the elements to fan out over, read again on every pass.
            Elements must be hashable: the arm book is kept by element, and
            that is what makes a difference computable.
        change: the change subscription that says the element set may have
            moved. Bound once, before the first pass, and held for as long as
            this runs.
        body: the arm, run once per element, concurrently with the others. A
            lambda over the element, or a tree reading it with ``Attr(item)``.
        item: the name to bind that arm's element under, for a tree body.
            Optional, defaults to ``"item"``; a lambda mints its own.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in. A term yielding an
            iterable of floats, or a literal one. Empty by default: re-checks
            are opt in (``after=nu.RECHECK_AFTER``).
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` (the default) turns them off; opt in with
            ``every=nu.RECHECK_EVERY``. A term yielding a float or None, or a
            literal one.

    Notes:
        - ``ForEachParAsync`` held open: the fan-out and the arms are the
          same, but the element list is read on every pass instead of once.
          What comes out of the comparison is births and deaths, and nothing
          else: an element with no arm gets one started, an arm whose element
          is gone is cancelled, and every other arm keeps running untouched.
          That is the whole reason to reach for this over a fan-out rebuilt
          from scratch, which restarts the innocent along with the guilty.
        - A death is a cancellation, delivered by this atom. An arm does not
          have to notice its own element leaving; it is cancelled where it
          stands, and drained before the pass that killed it returns.
        - So a delete and a re-add of the same element are a death and then a
          birth, in that order, never an overlap - but only when the two are
          seen by two different passes. A pass reconciles against the current
          answer to ``items``, it does not replay changes, so a delete and a
          re-add that both land between two passes leave the arm running and
          unaware.
        - An arm runs once per appearance of its element. One that finishes
          on its own stays finished: its element is remembered as done and
          gets no new arm while it stays in the read. Once the element has
          left a read and come back, it is born again. A body that should
          run again on its own terms wraps itself in ``Retry`` or loops.
        - An arm error ends the flow. The siblings are cancelled and drained,
          the subscription is unbound and closed, and the error propagates,
          like ``ForEachParAsync``'s first-error-wins. Isolate an arm with
          ``TryCatch`` and supervise it with ``Retry`` where that is wanted.
        - Never returns on its own, even with an empty ``items``: the
          surrounding Flow ends it by cancelling. Every live arm is cancelled
          and drained on the way out.
        - A ``body`` that writes into what ``change`` watches wakes this atom
          again, and the pass that follows finds the arm set already right.
        - A literal schedule that cannot run is refused at build time; a
          computed one is refused when it is read, with the same message.

    Yields:
        Nothing.

    Example:
        Following a live collection needs a real substrate behind the
        subscription, so it cannot run standalone here::

            ReconcileLatestEach(users.keys(), users.on_children_change(), lambda user: body)
    """

    _param_slots = Declared(value=frozenset({0, 1, 3, 4, 5}), name="param_slots")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(
        self,
        items: object,
        change: object,
        body: object,
        item: object = None,
        *,
        after: Iterable[float] | object = (),
        every: float | object | None = None,
    ) -> None:
        body, (item,) = bind("ReconcileLatestEach", body, item=item)
        super().__init__(
            items,
            change,
            body,
            "item" if item is None else item,
            *schedule_terms("ReconcileLatestEach", after, every),
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReconcileLatestEach")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        items = children[0]

        async def ids(rt: Runtime) -> list:
            return [elem async for elem in aiter_any(await items(rt))]

        async def athunk(rt: Runtime) -> None:
            await hold_arms("ReconcileLatestEach", rt, nid, children, ids)

        return athunk
