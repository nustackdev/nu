"""WaitUntil: wait until a condition holds."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.engine.structure import Declared
from nu.lang import Control

from .._body import async_only
from ._wakes import Wakes, read_schedule, schedule_terms


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.lang.runtime import Runtime

__all__ = ["WaitUntil"]


class WaitUntil(Control):
    """Wait until a condition holds, read after subscribing, on every change, and on re-checks.

    Binds the subscription once and evaluates ``cond`` right after, then
    again whenever a change lands or a re-check falls due. Returns on the
    first truthy read, so a condition that already holds returns at once.

    Args:
        change: the change subscription that says ``cond`` may have moved.
        cond: what to wait for. It gets no changed key: it reads the state
            and answers. A tree, or a lambda taking no arguments.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in. A term yielding an
            iterable of floats, or a literal one. Empty by default: re-checks
            are opt in (``after=nu.RECHECK_AFTER``).
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` (the default) turns them off, leaving a dropped
            notification to wait for the next change; opt in with
            ``every=nu.RECHECK_EVERY``. A term yielding a float or None, or a
            literal one.

    Notes:
        - The first read follows the subscribe, so a write made before the
          wait began is always seen. One whose notification goes missing is
          seen on the next re-check.
        - Changes landing while ``cond`` is read merge into one more read.
        - The subscription is unbound and closed on any exit.
        - A literal schedule that cannot run is refused at build time; a
          computed one is refused when it is read, with the same message.

    Yields:
        Nothing.

    Example:
        Block until a job is marked done. Needs a real substrate behind the
        subscription, so it cannot run standalone::

            WaitUntil(Job.status.on_change(), Job.status == "done")
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 1, 2, 3}), name="param_slots")

    def __init__(
        self,
        change: object,
        cond: object,
        *,
        after: Iterable[float] | object = (),
        every: float | object | None = None,
    ) -> None:
        cond, () = bind("WaitUntil", cond)
        super().__init__(change, cond, *schedule_terms("WaitUntil", after, every))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("WaitUntil")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        change, cond, after, every = children

        async def athunk(rt: Runtime) -> None:
            schedule = await read_schedule("WaitUntil", rt, after, every)
            async with Wakes(await change(rt), *schedule) as wakes:
                while True:
                    await wakes.wait()
                    if await cond(rt):
                        return

        return athunk
