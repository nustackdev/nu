"""ReactEvery: run the body on every change, in order, one at a time."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.engine.structure import Declared
from nu.lang import Control

from .._body import async_only, changed, drain_body


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["ReactEvery"]


class ReactEvery(Control):
    """Run the body on every change, unconditionally, forever.

    Binds to the change subscription once and then runs the body once per
    notification, with no condition to end the loop. Never returns on its
    own; the caller ends it by cancelling the surrounding task.

    Args:
        change: the change subscription to wait on.
        body: what to run on every notification: a lambda over the changed
            key, or a tree.
        changed_key: name the changed key is bound under while each run of
            a tree body lasts; a lambda mints its own.

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
    _param_slots = Declared(value=frozenset({0, 2}), name="param_slots")

    def __init__(
        self,
        change: object,
        body: object,
        *,
        changed_key: object = None,
    ) -> None:
        body, (changed_key,) = bind("ReactEvery", body, changed_key=changed_key)
        has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, changed_key)
        else:
            super().__init__(change, body)
        self._payload["has_changed_key"] = has_changed_key

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactEvery")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_ck = self._payload["has_changed_key"]

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            changed_key_name = await children[2](rt) if has_ck else None
            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                while True:
                    key = await queue.get()
                    with changed(rt.ctx.attrs, changed_key_name, key):
                        await drain_body(rt, children[1])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk
