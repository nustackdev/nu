"""ReactLatestEach: per key, a newer change restarts that key's body."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.engine.structure import Declared
from nu.lang import Control

from .._arms import ArmBook
from .._body import async_only, changed, drain_body


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["ReactLatestEach"]


class ReactLatestEach(Control):
    """Run the body per key, a newer change on a key restarting only that key's run.

    ``ReactLatest`` with one run per key. Binds to the change subscription
    once and starts the body as its own task on every notification. A run
    for that key still going when the next notification lands is cancelled
    and awaited until it has fully unwound, and only then does the body start
    again with the new notification; runs for other keys are not touched. A
    run that finishes on its own leaves the book, and the next notification
    for its key starts a fresh one. Never returns on its own; the caller ends
    it by cancelling the surrounding task.

    Args:
        change: the change subscription to wait on.
        body: what to run on every notification: a lambda over the changed
            key, or a tree. May never finish (a live view per key); the next
            change on that key is what ends it.
        changed_key: name the changed key is bound under while each run of
            a tree body lasts; a lambda mints its own.

    Notes:
        - Keys must be hashable: the book of runs is kept by key.
        - Notifications for a key that pile up while its cancelled run is
          unwinding are collapsed into the one restart; other keys' are
          kept, in order.
        - Restarts go one at a time: a slow unwind of one key's cancelled
          run holds the next notification for every key until it is done.
          Other keys' running bodies are not touched, only their next
          start waits.
        - Each run gets a fresh branch of the Context it started from: its
          own attrs key space, values shared by reference. A restarted body
          never sees attrs a cancelled run left behind, runs side by side
          never see each other's, and attrs a run binds do not reach the
          caller.
        - An error raised by the body, or while a cancelled run unwinds,
          ends the flow and propagates: every other run is cancelled and
          drained, then the subscription is unbound and closed. The
          cancellation from a restart is not an error. Isolate with
          ``TryCatch``, supervise with ``Retry``.
        - Cancelling the flow cancels and drains every running body before
          the subscription is unbound and closed.
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.

    Example:
        A live view per row, redrawn from scratch when that row changes.
        Needs a real substrate behind the subscription, so it cannot run
        standalone::

            ReactLatestEach(Rows.on_children_change(), lambda key: draw(key))
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
        body, (changed_key,) = bind("ReactLatestEach", body, changed_key=changed_key)
        names = () if changed_key is None else (changed_key,)
        super().__init__(change, body, *names)
        self._payload["has_changed_key"] = changed_key is not None

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactLatestEach")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_ck = self._payload["has_changed_key"]
        body = children[1]

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            inbox: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(inbox.put_nowait, k)

            changed_key_name = await children[2](rt) if has_ck else None

            def spawn(key: object) -> asyncio.Task:
                # Every run is a task of its own, on a fresh branch.
                run_rt = rt.branch()

                async def run() -> None:
                    with changed(run_rt.ctx.attrs, changed_key_name, key):
                        await drain_body(run_rt, body)

                return asyncio.ensure_future(run())

            book = ArmBook(spawn, owner="ReactLatestEach")
            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                while True:
                    key = await book.wait(inbox.get())
                    await book.restart(key)
                    # Whatever arrived for this key while the stale run
                    # unwound predates the fresh one, so it is covered; the
                    # rest stays queued, in order.
                    burst = []
                    while not inbox.empty():
                        burst.append(inbox.get_nowait())
                    for k in burst:
                        if k != key:
                            inbox.put_nowait(k)
            finally:
                await book.drain()
                sub.unbind(on_change)
                sub.close()

        return athunk
