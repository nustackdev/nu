"""ReconcileEach: each wake, one pass of the body per id, joining all."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.core._stream import aiter_any
from nu.core.flows.parallel._scheduling import aeval_foreach_par
from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.attributes.execution import ExecOrder

from .._body import async_only
from ._wakes import DEFAULT_AFTER, DEFAULT_EVERY, Wakes, read_schedule, schedule_terms


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.lang.runtime import Runtime

__all__ = ["ReconcileEach"]


class ReconcileEach(Control):
    """``ReconcileEach(items, change, lambda x: body)`` - each wake, one pass of ``body`` per element, all at once.

    ``Reconcile`` over a fan-out: each pass reads ``items`` and runs the body
    once per element, every arm on the loop at once, and joins on all of
    them before the pass is over. Passes run right after subscribing, on
    every change, and on re-checks, one at a time, with changes during a
    pass merged into one more.

    Args:
        items: the elements to fan out over, read again on every pass.
        change: the change subscription that says the state may have moved.
            Bound once, before the first pass, and held for as long as this
            runs.
        body: the pass for one element, run concurrently with the others. A
            lambda over the element, or a tree reading it with ``Attr(item)``.
            It gets no changed key: it reads the state it keeps in step for
            its element and makes it right.
        item: the name to bind that pass's element under, for a tree body.
            Optional, defaults to ``"item"``; a lambda mints its own.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in. A term yielding an
            iterable of floats, or a literal one.
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` turns them off. A term yielding a float or None, or a
            literal one.

    Notes:
        - A pass is ``ForEachParAsync`` over the current ``items``: one arm
          per element, joined on all, first error wins and the other arms
          are cancelled and drained. The arms of a pass are meant to finish;
          an arm that runs for good holds the pass open and every later wake
          waits behind it. For arms that stay up, use
          ``ReconcileLatestEach``.
        - An error from any arm ends the flow and propagates. The
          subscription is unbound and closed on any exit.
        - Elements are not compared across passes: every pass runs every
          element again, and an empty read runs nothing. Nor are they
          deduplicated within a pass: an element that ``items`` repeats
          gets one arm per repeat, as ``ForEachParAsync`` gives it. That is
          also why elements need not be hashable here, unlike the ids of
          ``ReconcileLatestEach``.
        - Never returns on its own: the surrounding Flow ends it by
          cancelling, which cancels and drains the arms of a pass under way.
        - A literal schedule that cannot run is refused at build time; a
          computed one is refused when it is read, with the same message.

    Yields:
        Nothing.

    Example:
        Keep every order's total in step with its lines. Needs a real
        substrate behind the subscription, so it cannot run standalone::

            ReconcileEach(orders.keys(), orders.on_descendants_change(), lambda o: retotal(o))
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
        after: Iterable[float] | object = DEFAULT_AFTER,
        every: float | object | None = DEFAULT_EVERY,
    ) -> None:
        body, (item,) = bind("ReconcileEach", body, item=item)
        super().__init__(
            items,
            change,
            body,
            "item" if item is None else item,
            *schedule_terms("ReconcileEach", after, every),
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReconcileEach")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        items, change, _body, item, after, every = children

        async def athunk(rt: Runtime) -> None:
            name = await item(rt)
            schedule = await read_schedule("ReconcileEach", rt, after, every)
            body_nid = rt.program.children[nid][2]
            async with Wakes(await change(rt), *schedule) as wakes:
                while True:
                    await wakes.wait()
                    elems = [elem async for elem in aiter_any(await items(rt))]
                    await aeval_foreach_par(rt, body_nid, elems, name)

        return athunk
