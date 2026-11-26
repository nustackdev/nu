"""ReactEvery: run the body on every change, in order, one at a time."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.binding import _DynamicBinding

from .._body import async_only, drain_body


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["ReactEvery"]


class ReactEvery(_DynamicBinding, Control):
    """Run the body on every change, unconditionally, forever.

    Binds to the change subscription once and then runs the body once per
    notification, with no condition to end the loop. Never returns on its
    own; the caller ends it by cancelling the surrounding task.

    Args:
        change: the change subscription to wait on.
        body: what to run on every notification: a lambda over the changed
            key, or a tree that reads none. Every run pushes a frame of its
            own holding its key.

    Notes:
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.

    Example:
        A body reading the key that changed. Needs a real substrate behind
        the subscription, so it cannot run standalone::

            ReactEvery(Cell.source.on_change(), lambda key: nu.print(key))
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(self, change: object, body: object) -> None:
        super().__init__(change, self._dynamic("ReactEvery", body, 1))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactEvery")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        binding = self._binding

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                while True:
                    key = await queue.get()
                    await drain_body(rt.on(binding.push(rt.ctx, (key,))), children[1])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk
