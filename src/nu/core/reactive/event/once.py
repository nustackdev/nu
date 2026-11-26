"""ReactOnce: wait for one change, run the body once, stop."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.binding import Binding

from .._body import async_only, drain_body


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["ReactOnce"]


class ReactOnce(Control):
    """Wait for one change on the subscription, run the body once, then stop.

    Binds to the change subscription, blocks until exactly one notification
    arrives, unbinds, and closes the subscription. The body (when present)
    runs once, after that single notification, before ``ReactOnce`` returns.

    Args:
        change: the change subscription to wait on (a ``Subscription``-yielding
            query, e.g. ``OnChange``).
        body: what to run once the change fires: a lambda over the changed
            key, or a tree that reads none. Optional: leave it out to just
            wait for one change and do nothing.

    Notes:
        - The run pushes a frame of its own holding the key.
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.

    Example:
        Running a body on the next click. Needs a real substrate behind the
        subscription, so it cannot run standalone::

            ReactOnce(Cell.clicked.on_change(), lambda key: nu.print(key))
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(self, change: object, body: object = None) -> None:
        if body is None:
            self._binding = Binding.none()
            super().__init__(change)
        else:
            body, self._binding = Binding.of_lambda("ReactOnce", body, 1)
            super().__init__(change, body)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactOnce")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_body = len(children) > 1  # [change, body?]
        binding = self._binding

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                key = await queue.get()
                if has_body:
                    await drain_body(rt.on(binding.push(rt.ctx, key)), children[1])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk
