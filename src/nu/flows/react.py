"""Reactive control flows: React, ReactWhile, ReactForever.

Subscribe to a change event and run a body in response. All three are
``Control`` flows: they drive a mutating body under query parameters (a
change subscription, a condition) and yield nothing, exactly like ``WhileDo``
/ ``ForeverDo``. A change notification is bridged into async via
``asyncio.Queue`` (one wake per notification, no collapsing), so all three
require an async runtime and raise from their sync ``_compile`` path.

``param_slots`` names the consumed queries (the change subscription at slot
0, a condition where present, an optional ``changed_key`` name); the
remaining slot is the body.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any
from nu.engine.structure import Declared
from nu.lang import Control


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["React", "ReactForever", "ReactWhile"]


async def _adrain_body(rt: Runtime, body_thunk: Callable) -> None:
    """Run a react body once and pull any values it yields through to completion.

    Args:
        rt: the runtime to run the body under.
        body_thunk: the compiled body thunk to await.

    Notes:
        - A body may be a Command (returns ``None``) or a stream (returns an
          iterable / async-iterable). Commands carry their writes and stop
          here; a stream's values must be drained to fire the side effects
          riding along with them, since nothing else pulls on them.

    Yields:
        Nothing. Always returns ``None``.
    """
    result = await body_thunk(rt)
    if result is None:
        return
    async for _ in aiter_any(result):
        pass


class React(Control):
    """Wait for one change on the subscription, run the body once, then stop.

    Binds to the change subscription, blocks until exactly one notification
    arrives, unbinds, and closes the subscription. The body (when present)
    runs once, after that single notification, before ``React`` returns.

    Args:
        change: the change subscription to wait on (a ``Subscription``-yielding
            query, e.g. ``OnChange``).
        body: what to run once the change fires. Optional: leave it out to
            just wait for one change and do nothing.
        changed_key: name to bind the changed key under (via the attrs
            side-channel) before the body runs. Requires a body.

    Notes:
        - Requires a body when ``changed_key`` is given: capturing a key with
          nothing to run it against is meaningless.
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.
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
        if changed_key is not None and body is None:
            msg = "React changed_key requires a body"
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
        def thunk(rt: Runtime) -> None:
            msg = "React requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

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
                if changed_key_name is not None:
                    rt.ctx.attrs[changed_key_name] = key
                if has_body:
                    await _adrain_body(rt, children[1])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk


class ReactWhile(Control):
    """Run the body on each change while the condition stays truthy.

    Binds to the change subscription once, then on every notification checks
    the condition first: false stops the loop and unbinds without running the
    body for that notification; truthy runs the body and waits for the next
    change. The condition is re-evaluated fresh on every notification, not
    just once at the start.

    Args:
        change: the change subscription to wait on.
        condition: checked after each notification, before that turn's body
            runs. A falsy value ends the loop.
        body: what to run on a turn where the condition holds.
        changed_key: name to bind the changed key under before the body runs
            on that turn.

    Notes:
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 1, 3}), name="param_slots")

    def __init__(
        self,
        change: object,
        condition: object,
        body: object,
        *,
        changed_key: object = None,
    ) -> None:
        has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, condition, body, changed_key)
        else:
            super().__init__(change, condition, body)
        self._payload["has_changed_key"] = has_changed_key

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ReactWhile requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_ck = self._payload["has_changed_key"]

        async def athunk(rt: Runtime) -> None:
            changed_key_name = await children[3](rt) if has_ck else None
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                while True:
                    key = await queue.get()
                    if not await children[1](rt):
                        break
                    if changed_key_name is not None:
                        rt.ctx.attrs[changed_key_name] = key
                    await _adrain_body(rt, children[2])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk


class ReactForever(Control):
    """Run the body on every change, unconditionally, forever.

    Binds to the change subscription once and then runs the body once per
    notification, with no condition to end the loop. Never returns on its
    own; the caller ends it by cancelling the surrounding task.

    Args:
        change: the change subscription to wait on.
        body: what to run on every notification.
        changed_key: name to bind the changed key under before each body run.

    Notes:
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.
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
        has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, changed_key)
        else:
            super().__init__(change, body)
        self._payload["has_changed_key"] = has_changed_key

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ReactForever requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

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
                    if changed_key_name is not None:
                        rt.ctx.attrs[changed_key_name] = key
                    await _adrain_body(rt, children[1])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk
