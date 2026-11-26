"""ReactWhile: run the body on each change while a condition holds."""

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

__all__ = ["ReactWhile"]


class ReactWhile(Control):
    """Run the body on each change while the condition stays truthy.

    Binds to the change subscription once, then on every notification checks
    the condition first: false stops the loop and unbinds without running the
    body for that notification; truthy runs the body and waits for the next
    change. The condition is re-evaluated fresh on every notification, not
    just once at the start.

    The condition sees the changed key as the body does, so a loop can wait
    out the changes it does not care about and end on the first one it does.

    Args:
        change: the change subscription to wait on.
        condition: checked after each notification, before that turn's body
            runs: a lambda over the changed key, or a tree that reads none. A
            falsy value ends the loop.
        body: what to run on a turn where the condition holds: a lambda over
            the changed key, or a tree that reads none.

    Notes:
        - The condition and the body are two bindings, each over its own
          lambda and its own Shape. Every turn pushes a frame holding the
          key for each.
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Example:
        Wait for the first change to a key the caller cares about::

            ReactWhile(Space.cells.on_descendants_change("*", "prog"),
                       lambda key: mine.contains(key).not_(),
                       nu.Noop())

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 1}), name="param_slots")

    def __init__(self, change: object, condition: object, body: object) -> None:
        condition, self.condition_binding = Binding.of_lambda("ReactWhile condition", condition, 1)
        body, self.body_binding = Binding.of_lambda("ReactWhile body", body, 1)
        super().__init__(change, condition, body)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactWhile")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        change, condition, body = children
        cond_b, body_b = self.condition_binding, self.body_binding

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            sub = await change(rt)
            sub.bind(on_change)
            try:
                while True:
                    key = await queue.get()
                    if not await condition(rt.on(cond_b.push(rt.ctx, key))):
                        break
                    await drain_body(rt.on(body_b.push(rt.ctx, key)), body)
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk
