"""Wakes for a level flow: one held subscription plus a re-check schedule.

A level body reads current state and makes it right, so it does not care why
it runs. That is what lets this helper add wakes no subscription delivered:
one right after binding, so the first read always follows the subscribe, and,
when the flow opts in, re-checks on a schedule, so a notification that never
arrived (a writer that had not yet learnt of a fresh subscription, a dropped
message) is caught late rather than never.

Private on purpose. A wake carries no changed key, so feeding these into an
event flow, whose body is promised the real key of a real change, would break
that promise. Only the level flows hold a ``Wakes``.

The schedule itself is two child terms of the flow, ``after`` (an iterable of
float offsets) and ``every`` (a float or None). Both are off unless the flow
is given them: ``RECHECK_AFTER`` and ``RECHECK_EVERY`` are the standard
schedule to opt into. ``schedule_terms`` checks and normalises literal ones
at build time; ``read_schedule`` evaluates them at run time and checks
computed ones with the same messages.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any
from nu.lang import Literal, Nu


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from types import TracebackType

    from nu.core.reactive.protocol import Subscription
    from nu.lang.runtime import Runtime

__all__ = [
    "RECHECK_AFTER",
    "RECHECK_EVERY",
    "Wakes",
    "check_after",
    "check_every",
    "check_schedule",
    "read_schedule",
    "schedule_terms",
]


#: The standard early re-checks to opt into, in seconds after binding. They
#: cover the window in which writers may not yet know about a fresh
#: subscription. A level flow takes none unless given ``after=``.
RECHECK_AFTER: tuple[float, ...] = (0.1, 0.3, 1.0)

#: The standard standing re-check period to opt into, in seconds. It bounds how
#: long a dropped notification can go unnoticed. A level flow takes none unless
#: given ``every=``.
RECHECK_EVERY: float = 30.0


def check_after(owner: str, after: Iterable[float]) -> tuple[float, ...]:
    """The ``after`` offsets as a flow keeps them: a sorted tuple of floats.

    Raises:
        ValueError: a negative delay.
    """
    delays = tuple(sorted(float(d) for d in after))
    if delays and delays[0] < 0:
        msg = f"{owner}: after= delays must not be negative, got {delays}"
        raise ValueError(msg)
    return delays


def check_every(owner: str, every: float | None) -> float | None:
    """The ``every`` period as a flow keeps it: a float, or None.

    Raises:
        ValueError: a period that is not positive (it would spin).
    """
    if every is not None and every <= 0:
        msg = f"{owner}: every= must be positive or None, got {every}"
        raise ValueError(msg)
    return None if every is None else float(every)


def check_schedule(
    owner: str, after: Iterable[float], every: float | None
) -> tuple[tuple[float, ...], float | None]:
    """The re-check schedule as a flow keeps it; raises on one that cannot run.

    Returns:
        ``after`` as a sorted tuple of floats, ``every`` as a float or None.

    Raises:
        ValueError: a negative ``after`` delay, or an ``every`` that is not
            positive (it would spin).
    """
    return check_after(owner, after), check_every(owner, every)


def _literal(term: object) -> tuple[bool, object]:
    """Whether ``term`` is known at build time, and its value when it is."""
    if isinstance(term, Literal):
        return True, term._payload["value"]
    if isinstance(term, Nu):
        return False, None
    return True, term


def schedule_terms(owner: str, after: object, every: object) -> tuple[object, object]:
    """``after`` and ``every`` as the child terms a level flow holds.

    A literal (a raw value or a ``Literal``) is checked now and kept
    normalised, so a schedule that cannot run is refused at build time. Any
    other term is kept as given and checked by ``read_schedule`` when it runs.

    Raises:
        ValueError: a literal schedule that cannot run.
    """
    known, value = _literal(after)
    if known:
        after = Literal(check_after(owner, value))
    known, value = _literal(every)
    if known:
        every = Literal(check_every(owner, value))
    return after, every


async def read_schedule(
    owner: str, rt: Runtime, after: Callable, every: Callable
) -> tuple[tuple[float, ...], float | None]:
    """Evaluate the ``after`` and ``every`` children and check what they yield.

    Raises:
        ValueError: a schedule that cannot run, with the build-time messages.
    """
    delays = [d async for d in aiter_any(await after(rt))]
    return check_schedule(owner, delays, await every(rt))


def _due(start: float, after: tuple[float, ...], every: float | None) -> Iterator[float]:
    """Loop times the re-checks fall on: ``after`` offsets, then every ``every`` forever."""
    last = start
    for delay in after:
        last = start + delay
        yield last
    if every is None:
        return
    while True:
        last += every
        yield last


class Wakes:
    """Wakes for one level flow, from a subscription it holds for its whole life.

    Used as ``async with Wakes(sub, after, every) as wakes`` and then
    ``await wakes.wait()`` before each pass. The first wait returns at once,
    after the subscription is bound. Every later one returns once something
    asked for a pass since the previous one returned: a notification or a
    due re-check.

    Wakes merge. Asking is setting one flag, not queueing, so any number of
    notifications landing while a pass runs cost exactly one more pass. A
    pass that starts after the asking reads everything that was asked about.

    Re-checks are measured from binding: one at each ``after`` offset, then
    one every ``every`` seconds after the last of them, forever (``None``
    stops after ``after``). With neither, the bind wake and notifications
    are all. Exiting the block cancels the pending re-check,
    unbinds and closes the subscription. It is never reopened: reopening
    would open a fresh window for writes to slip through.
    """

    def __init__(
        self,
        sub: Subscription,
        after: tuple[float, ...] = (),
        every: float | None = None,
    ) -> None:
        self._sub = sub
        self._after = after
        self._every = every
        self._asked = asyncio.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._times: Iterator[float] = iter(())
        self._timer: asyncio.TimerHandle | None = None

    async def __aenter__(self) -> Wakes:
        self._loop = asyncio.get_running_loop()
        self._sub.bind(self._on_change)
        self._times = _due(self._loop.time(), self._after, self._every)
        self._schedule()
        self._asked.set()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self._sub.unbind(self._on_change)
        self._sub.close()

    async def wait(self) -> None:
        """Return once a pass is owed, and take it: asks until now are spent."""
        await self._asked.wait()
        self._asked.clear()

    def _on_change(self, key: object) -> None:
        # The key is dropped here, at the edge: nothing past this point can
        # see what changed. A backend may call from its own thread.
        del key
        loop = self._loop
        if loop is not None:
            loop.call_soon_threadsafe(self._asked.set)

    def _recheck(self) -> None:
        self._asked.set()
        self._schedule()

    def _schedule(self) -> None:
        due = next(self._times, None)
        loop = self._loop
        self._timer = None if due is None or loop is None else loop.call_at(due, self._recheck)
