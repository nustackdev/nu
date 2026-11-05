"""ReactWhile: run the body on each change while a condition holds."""

from __future__ import annotations

import asyncio
from contextlib import ExitStack
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.engine.structure import Declared
from nu.lang import Control

from .._body import async_only, changed, drain_body


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
            runs: a lambda over the changed key, or a tree. A falsy value
            ends the loop.
        body: what to run on a turn where the condition holds: a lambda over
            the changed key, or a tree.
        changed_key: name the changed key is bound under while that turn's
            tree condition and tree body run; a lambda mints its own.

    Notes:
        - The key is bound for the whole turn, condition and body alike. A
          lambda condition and a lambda body each read it under the name
          their own code mints.
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
    _param_slots = Declared(value=frozenset({0, 1, 3, 4}), name="param_slots")

    def __init__(
        self,
        change: object,
        condition: object,
        body: object,
        *,
        changed_key: object = None,
    ) -> None:
        condition, (condition_key,) = bind("ReactWhile", condition, changed_key=changed_key)
        body, (body_key,) = bind("ReactWhile", body, changed_key=changed_key)
        # One name when both are trees: the given ``changed_key``, or none.
        pair = (condition_key,) if condition_key is body_key else (condition_key, body_key)
        names = tuple(name for name in pair if name is not None)
        super().__init__(change, condition, body, *names)
        self._payload["key_names"] = len(names)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactWhile")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name_slots = children[3 : 3 + self._payload["key_names"]]

        async def athunk(rt: Runtime) -> None:
            names = [await slot(rt) for slot in name_slots]
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                while True:
                    key = await queue.get()
                    with ExitStack() as turn:
                        for name in names:
                            turn.enter_context(changed(rt.ctx.attrs, name, key))
                        if not await children[1](rt):
                            break
                        await drain_body(rt, children[2])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk
