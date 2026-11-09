"""ReconcileWhile: one pass per wake while a condition holds."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.engine.structure import Declared
from nu.lang import Control

from .._body import async_only, drain_body
from ._wakes import Wakes, read_schedule, schedule_terms


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.lang.runtime import Runtime

__all__ = ["ReconcileWhile"]


class ReconcileWhile(Control):
    """Keep state right while a condition holds: each wake reads ``cond``, a falsy read returns, a truthy one runs the body.

    Binds the subscription once and reads ``cond`` right after, then again
    whenever a change lands or a re-check falls due. A truthy read runs one
    pass of ``body``; the first falsy read ends the flow. ``Reconcile`` with
    an exit, and the level twin of ``ReactWhile``.

    Args:
        change: the change subscription that says the state may have moved.
        cond: whether to keep going. It gets no changed key: it reads the
            state and answers. A tree, or a lambda taking no arguments. The
            absent sentinel counts as false.
        body: the pass, run after each truthy read. It gets no changed key
            either: it reads the state it keeps in step and makes it right.
            A tree, or a lambda taking no arguments.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in. A term yielding an
            iterable of floats, or a literal one. Empty by default: re-checks
            are opt in (``after=nu.RECHECK_AFTER``).
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` (the default) turns them off; opt in with
            ``every=nu.RECHECK_EVERY``. A term yielding a float or None, or a
            literal one.

    Notes:
        - ``WaitUntil(c, x)`` is ``ReconcileWhile(c, Not(x), Noop())``: a
          wait is a loop with nothing to do.
        - Replaces a ``WhileDo`` around a ``WaitUntil``, which would open a
          fresh subscription every turn and a blind window with it. Here the
          subscription is bound once and held until the condition fails.
        - Changes landing while ``cond`` is read or a pass runs merge into
          one more read.
        - A body that writes into what ``change`` watches wakes the flow
          again, so a body that moves the state towards the exit drives
          itself there.
        - An error raised by ``cond`` or ``body`` ends the flow and
          propagates. The subscription is unbound and closed on any exit.
        - A literal schedule that cannot run is refused at build time; a
          computed one is refused when it is read, with the same message.

    Yields:
        Nothing.

    Example:
        Top a stock up, one unit per pass, until it is full. Needs a real
        substrate behind the subscription, so it cannot run standalone::

            ReconcileWhile(Stock.n.on_change(), Stock.n < 10, Stock.n.set(Stock.n + 1))
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 1, 3, 4}), name="param_slots")

    def __init__(
        self,
        change: object,
        cond: object,
        body: object,
        *,
        after: Iterable[float] | object = (),
        every: float | object | None = None,
    ) -> None:
        cond, () = bind("ReconcileWhile", cond)
        body, () = bind("ReconcileWhile", body)
        super().__init__(change, cond, body, *schedule_terms("ReconcileWhile", after, every))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReconcileWhile")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        change, cond, body, after, every = children

        async def athunk(rt: Runtime) -> None:
            schedule = await read_schedule("ReconcileWhile", rt, after, every)
            async with Wakes(await change(rt), *schedule) as wakes:
                while True:
                    await wakes.wait()
                    if not await cond(rt):
                        return
                    await drain_body(rt, body)

        return athunk
