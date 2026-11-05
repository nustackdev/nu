"""Test doubles for the reactive flows: a hand-fired subscription and coroutine terms.

Reactive tests need a substrate. Most of them do without a real one: a
``Feed`` is the ``Subscription`` the flow binds, placed in ctx attrs and read
back with ``nu.context.Attr("feed")`` as the flow's ``change`` child, and the
test fires it by hand (and can drop notifications). ``Body`` and ``Read`` turn
a Python coroutine into an async-only action or query, so each test decides
when a change lands, which one is lost, and when a pass may finish.

Waits are event-driven with generous deadlines; nothing asserts a wall-clock
bound.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from nu.core.reactive.level._wakes import Wakes
from nu.engine.structure import Declared
from nu.lang import Context, ScalarAction, ScalarQuery
from nu.lang.helpers import arun


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "QUIET",
    "Body",
    "Feed",
    "Read",
    "live_rechecks",
    "settle_loop",
    "start",
    "stop",
    "until",
]


#: No re-checks at all: only the wake after binding and real notifications.
QUIET: dict = {"after": (), "every": None}


class Feed:
    """A Subscription the test fires by hand, able to drop notifications.

    Records bind / unbind / close in ``log``. Survives the deep copy a scope
    carry makes of attrs, so the handle the flow binds is the one the test
    holds.
    """

    def __init__(self, log: list | None = None) -> None:
        self.receivers: list = []
        self.closed = False
        self.dropping = 0
        self.log = [] if log is None else log

    def __deepcopy__(self, memo: dict) -> Feed:
        return self

    def bind(self, receiver: Callable) -> None:
        self.log.append("bind")
        self.receivers.append(receiver)

    def unbind(self, receiver: Callable) -> None:
        self.log.append("unbind")
        self.receivers.remove(receiver)

    def close(self) -> None:
        self.log.append("close")
        self.closed = True

    def fire(self, key: object = "k") -> None:
        if self.dropping:
            self.dropping -= 1
            return
        for receiver in list(self.receivers):
            receiver(key)


class Body(ScalarAction):
    """Async-only body running ``fn(rt)``."""

    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fn: Callable) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "Body was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return await fn(rt)

        return athunk


class Read(ScalarQuery):
    """Async-only read answering ``fn(rt)``: a condition or an element list."""

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, fn: Callable) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "Read was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return await fn(rt)

        return athunk


def start(term: object, **attrs: object) -> asyncio.Task:
    """Run ``term`` as a task, with ``attrs`` (a ``feed=Feed()``, say) in ctx."""
    return asyncio.ensure_future(arun(term, Context(attrs=attrs)))


async def until(check: Callable[[], bool], timeout: float = 5.0) -> None:
    """Poll ``check`` until it holds; fail on the deadline."""

    async def poll() -> None:
        while not check():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(poll(), timeout)


async def stop(task: asyncio.Task) -> None:
    """Cancel a flow that never returns on its own and see it end cancelled."""
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def settle_loop() -> None:
    """Let deliveries scheduled with call_soon_threadsafe land."""
    for _ in range(5):
        await asyncio.sleep(0)


def live_rechecks() -> list:
    """Re-check timers still armed on the running loop, from any ``Wakes``."""
    loop = asyncio.get_running_loop()
    return [
        h
        for h in loop._scheduled  # type: ignore[attr-defined]
        if not h.cancelled() and isinstance(getattr(h._callback, "__self__", None), Wakes)
    ]
