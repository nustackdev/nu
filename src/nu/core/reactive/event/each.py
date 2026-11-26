"""ReactEach: run the body on every change, in order per key, keys side by side."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.binding import Binding

from .._body import async_only, drain_body
from ._keyed import KeyedQueues


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["ReactEach"]


class ReactEach(Control):
    """Run the body on every change, in order within a key, keys side by side.

    ``ReactEvery`` with one queue per key. Binds to the change subscription
    once and runs the body once per notification: notifications for the same
    key run one after the other, in the order they arrived, and notifications
    for different keys run at the same time. A key whose queue has drained
    holds nothing until it is notified again. Never returns on its own; the
    caller ends it by cancelling the surrounding task.

    Args:
        change: the change subscription to wait on.
        body: what to run on every notification: a lambda over the changed
            key, or a tree that reads none. Every run pushes a frame of its
            own holding its key.

    Notes:
        - Keys must be hashable: the queues are kept by key.
        - Each run pushes its own frame on the reaction's frames, values
          shared by reference. Runs side by side never see each other's
          frames, and a frame a run pushes never reaches the caller.
        - Memory is bounded by the backlog per key, as ``ReactEvery``'s queue
          is: a key notified faster than its body runs piles notifications up.
        - An error raised by the body ends the flow and propagates: every
          other run is cancelled and drained, then the subscription is unbound
          and closed. Isolate with ``TryCatch``, supervise with ``Retry``.
        - Cancelling the flow cancels and drains every running body before
          the subscription is unbound and closed.
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.

    Example:
        Handling writes per row, rows side by side. Needs a real substrate
        behind the subscription, so it cannot run standalone::

            ReactEach(Rows.on_children_change(), lambda key: handle(key))
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(self, change: object, body: object) -> None:
        body, self._binding = Binding.of_lambda("ReactEach", body, 1)
        super().__init__(change, body)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactEach")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[1]
        binding = self._binding

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            inbox: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(inbox.put_nowait, k)

            async def run(key: object) -> None:
                # Every run pushes a frame of its own: runs side by side never
                # see each other's key.
                await drain_body(rt.on(binding.push(rt.ctx, key)), body)

            queues = KeyedQueues(run, owner="ReactEach")
            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                while True:
                    await queues.put(await queues.wait(inbox.get()))
            finally:
                await queues.drain()
                sub.unbind(on_change)
                sub.close()

        return athunk
