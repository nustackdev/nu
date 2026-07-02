"""Reactive control flows — React, ReactWhile, ReactForever.

Subscribe to change events and run a body in response. All three are ``Control``
flows: they drive a mutating body under query parameters (a change
subscription, a condition) and **yield nothing** — the body carries the writes,
exactly like ``WhileDo`` / ``ForeverDo``. A change notification is bridged into
async via ``asyncio.Queue`` (one wake per notification, no collapsing).

``param_slots`` names the consumed queries (the change subscription at slot 0, a
condition, an optional ``changed_key`` name); the remaining slot is the body.
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


class React(Control):
    """Wait for one change event, run body once; yields nothing.

    Children ``[change, body?, changed_key?]``: slot 0 is the change
    subscription (param), the optional body slot carries the writes, and an
    optional ``changed_key`` name (last slot, param) captures the changed key.
    A ``changed_key`` requires a body — capturing the key with nothing to run is
    meaningless — so the body always sits at slot 1 when present.
    """

    mutates = Declared(value=frozenset())
    requires_async = Declared(value=True)
    param_slots = Declared(value=frozenset({0, 2}))

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
        self.payload["has_body"] = body is not None
        self.payload["has_changed_key"] = changed_key is not None

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> None:
            msg = "React requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        has_body = self.payload["has_body"]
        ck_idx = 2 if self.payload["has_changed_key"] else None

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
                    async for _ in aiter_any(await children[1](rt)):
                        pass
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk


class ReactWhile(Control):
    """Run body on each change event while condition is truthy; yields nothing.

    Children ``[change, condition, body, changed_key?]``: slots 0 (change
    subscription), 1 (condition), and the optional ``changed_key`` at slot 3 are
    consumed queries; slot 2 is the body that carries the writes.
    """

    mutates = Declared(value=frozenset())
    requires_async = Declared(value=True)
    param_slots = Declared(value=frozenset({0, 1, 3}))

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
        self.payload["has_changed_key"] = has_changed_key

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> None:
            msg = "ReactWhile requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        has_ck = self.payload["has_changed_key"]

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
                    async for _ in aiter_any(await children[2](rt)):
                        pass
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk


class ReactForever(Control):
    """Run body on every change event; runs forever, yields nothing.

    Children ``[change, body, changed_key?]``: slot 0 (change subscription) and
    the optional ``changed_key`` at slot 2 are consumed queries; slot 1 is the
    body that carries the writes.
    """

    mutates = Declared(value=frozenset())
    requires_async = Declared(value=True)
    param_slots = Declared(value=frozenset({0, 2}))

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
        self.payload["has_changed_key"] = has_changed_key

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> None:
            msg = "ReactForever requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        has_ck = self.payload["has_changed_key"]

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
                    async for _ in aiter_any(await children[1](rt)):
                        pass
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk
