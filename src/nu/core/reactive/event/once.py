"""ReactOnce: wait for one change, run the body once, stop."""

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
            key, or a tree. Optional: leave it out to just wait for one
            change and do nothing.
        changed_key: name the changed key is bound under while a tree body
            runs. Requires a body; a lambda mints its own.

    Notes:
        - Requires a body when ``changed_key`` is given: capturing a key with
          nothing to run it against is meaningless.
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
    _param_slots = Declared(value=frozenset({0, 2}), name="param_slots")

    def __init__(
        self,
        change: object,
        body: object = None,
        *,
        changed_key: object = None,
    ) -> None:
        body, (changed_key,) = bind("ReactOnce", body, changed_key=changed_key)
        if changed_key is not None and body is None:
            msg = "ReactOnce changed_key requires a body"
            raise ValueError(msg)
        children: list = [change]
        if body is not None:
            children.append(body)
        if changed_key is not None:
            children.append(changed_key)
        super().__init__(*children)
        self._payload["has_body"] = body is not None
        self._payload["has_changed_key"] = changed_key is not None

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactOnce")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_body = self._payload["has_body"]
        ck_idx = 2 if self._payload["has_changed_key"] else None

        async def athunk(rt: Runtime) -> None:
            changed_key_name = await children[ck_idx](rt) if ck_idx is not None else None
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                key = await queue.get()
                if has_body:
                    with changed(rt.ctx.attrs, changed_key_name, key):
                        await drain_body(rt, children[1])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk
