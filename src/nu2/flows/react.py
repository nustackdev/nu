"""Reactive control flows — React, ReactWhile, ReactForever.

Subscribe to change events and execute body in response. Bridges callback
notifications into async via asyncio.Queue (one wake per notification, no
collapsing).

React and ReactWhile are ``StreamQuery``: they observe a subscription handle
and yield body results without introducing fabric writes of their own. The
body's own mutations are tracked by body terms. ReactForever is ``Control``:
it runs forever and yields nothing.

v1 reference: ``src/nu/shapes/flows/react.py``.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu2.core._stream import aiter_any
from nu2.engine.structure import Declared
from nu2.lang import Control, StreamQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["React", "ReactForever", "ReactWhile"]


class React(StreamQuery):
    """Wait for one change event, execute body once; yields stream of body results."""

    def __init__(
        self,
        change: object,
        body: object = None,
        *,
        changed_key: object = None,
    ) -> None:
        children: list = [change]
        self._body_idx: int | None = None
        self._changed_key_idx: int | None = None
        if body is not None:
            self._body_idx = len(children)
            children.append(body)
        if changed_key is not None:
            self._changed_key_idx = len(children)
            children.append(changed_key)
        super().__init__(*children)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        msg = "React requires async runtime"
        raise NotImplementedError(msg)

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body_idx = self._body_idx
        ck_idx = self._changed_key_idx

        async def athunk(rt: Runtime) -> object:
            changed_key_name = await children[ck_idx](rt) if ck_idx is not None else None

            async def agen() -> object:
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
                    if body_idx is not None:
                        async for v in aiter_any(await children[body_idx](rt)):
                            yield v
                finally:
                    sub.unbind(on_change)
                    sub.close()

            return agen()

        return athunk


class ReactWhile(StreamQuery):
    """Execute body on each change event while condition is truthy; yields body results."""

    def __init__(
        self,
        change: object,
        condition: object,
        body: object,
        *,
        changed_key: object = None,
    ) -> None:
        self._has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, condition, body, changed_key)
        else:
            super().__init__(change, condition, body)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        msg = "ReactWhile requires async runtime"
        raise NotImplementedError(msg)

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        has_ck = self._has_changed_key

        async def athunk(rt: Runtime) -> object:
            changed_key_name = await children[3](rt) if has_ck else None

            async def agen() -> object:
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
                        async for v in aiter_any(await children[2](rt)):
                            yield v
                finally:
                    sub.unbind(on_change)
                    sub.close()

            return agen()

        return athunk


class ReactForever(Control):
    """Execute body on every change event; runs forever, never returns."""

    mutates = Declared(value=frozenset())

    def __init__(
        self,
        change: object,
        body: object,
        *,
        changed_key: object = None,
    ) -> None:
        self._has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, changed_key)
        else:
            super().__init__(change, body)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        msg = "ReactForever requires async runtime"
        raise NotImplementedError(msg)

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        has_ck = self._has_changed_key

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
