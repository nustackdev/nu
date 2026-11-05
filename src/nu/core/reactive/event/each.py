"""ReactEach: run the body on every change, in order per key, keys side by side."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.engine.structure import Declared
from nu.lang import Control

from .._body import async_only, changed, drain_body
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
            key, or a tree.
        changed_key: name the changed key is bound under while each run of
            a tree body lasts; a lambda mints its own.

    Notes:
        - Keys must be hashable: the queues are kept by key.
        - Each run gets a fresh branch of the Context it started from: its
          own attrs key space, values shared by reference. Runs side by side
          never see each other's attrs, and attrs a run binds do not reach
          the caller.
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
    _param_slots = Declared(value=frozenset({0, 2}), name="param_slots")

    def __init__(
        self,
        change: object,
        body: object,
        *,
        changed_key: object = None,
    ) -> None:
        body, (changed_key,) = bind("ReactEach", body, changed_key=changed_key)
        names = () if changed_key is None else (changed_key,)
        super().__init__(change, body, *names)
        self._payload["has_changed_key"] = changed_key is not None

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactEach")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_ck = self._payload["has_changed_key"]
        body = children[1]

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            inbox: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(inbox.put_nowait, k)

            changed_key_name = await children[2](rt) if has_ck else None

            async def run(key: object) -> None:
                # Every run is on a fresh branch: runs side by side must not
                # share the name the key is bound under.
                run_rt = rt.branch()
                with changed(run_rt.ctx.attrs, changed_key_name, key):
                    await drain_body(run_rt, body)

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
