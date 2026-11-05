"""Reconcile: keep state right, one pass per wake."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.engine.structure import Declared
from nu.lang import Control

from .._body import async_only, drain_body
from ._wakes import DEFAULT_AFTER, DEFAULT_EVERY, Wakes, read_schedule, schedule_terms


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.lang.runtime import Runtime

__all__ = ["Reconcile"]


class Reconcile(Control):
    """Keep state right: run the body after subscribing, on every change, and on re-checks.

    Binds the subscription once and runs the body right after, then again
    whenever a change lands or a re-check falls due, one pass at a time.
    Never returns on its own; the caller ends it by cancelling.

    Args:
        change: the change subscription that says the state may have moved.
        body: the pass. It gets no changed key: it reads the state it keeps
            in step and makes it right, and does nothing when nothing is
            off. A tree, or a lambda taking no arguments.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in. A term yielding an
            iterable of floats, or a literal one.
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` turns them off. A term yielding a float or None, or a
            literal one.

    Notes:
        - Changes landing while a pass runs merge into one more pass.
        - A body that writes into what ``change`` watches wakes the flow
          again. A level body settles: the next pass finds nothing to do.
        - An error raised by the body ends the flow and propagates. The
          subscription is unbound and closed on any exit.
        - A literal schedule that cannot run is refused at build time; a
          computed one is refused when it is read, with the same message.

    Yields:
        Nothing.

    Example:
        Keep an order's total in step with its quantity. Needs a real
        substrate behind the subscription, so it cannot run standalone::

            Reconcile(Order.qty.on_change(), Order.total.set(Order.qty * Order.price))
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 2, 3}), name="param_slots")

    def __init__(
        self,
        change: object,
        body: object,
        *,
        after: Iterable[float] | object = DEFAULT_AFTER,
        every: float | object | None = DEFAULT_EVERY,
    ) -> None:
        body, () = bind("Reconcile", body)
        super().__init__(change, body, *schedule_terms("Reconcile", after, every))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("Reconcile")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        change, body, after, every = children

        async def athunk(rt: Runtime) -> None:
            schedule = await read_schedule("Reconcile", rt, after, every)
            async with Wakes(await change(rt), *schedule) as wakes:
                while True:
                    await wakes.wait()
                    await drain_body(rt, body)

        return athunk
