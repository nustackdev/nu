"""Reactive control flows - React, ReactForever, ReactWhile.

Subscribe to change events and execute children in response.
Uses ChangeOp ops from shapes.ops to obtain subscription
handles, then bridges callback-based notifications into async via
asyncio.Queue (one wake per notification, no collapsing).

React:         Wait for a single change, optionally execute body once.
ReactForever:  Execute body on every change (runs forever).
ReactWhile:    Execute body on each change while condition is truthy.
"""

from __future__ import annotations

import asyncio
from contextlib import aclosing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms import Interaction, Mode

from ..reactive import ChangeOp  # noqa: TC001 - runtime dependency


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu import Context, Nu
    from nu.terms import StrArg


__all__ = [
    "React",
    "ReactForever",
    "ReactWhile",
]


class React(Interaction):
    """Wait for a single change, then execute body once.

    Children layout: [change, body?, changed_key?]
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(
        self,
        change: ChangeOp,
        body: Nu | None = None,
        *,
        changed_key: StrArg | None = None,
    ) -> None:
        self._has_changed_key = changed_key is not None
        children: list = [change]
        if body is not None:
            children.append(body)
        self._body_idx = 1 if body is not None else None
        if changed_key is not None:
            self._changed_key_idx = len(children)
            children.append(changed_key)
        else:
            self._changed_key_idx = None
        super().__init__(*children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()

        def on_change(changed_key: object) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, changed_key)

        changed_key_name: str | None = None
        if self._changed_key_idx is not None:
            changed_key_name = await self.children[self._changed_key_idx].afirst(ctx)

        sub = await self.children[0].afirst(ctx)
        sub.bind(on_change)
        try:
            key = await queue.get()

            if changed_key_name is not None:
                ctx.attrs[changed_key_name] = key

            if self._body_idx is not None:
                async with aclosing(self.children[self._body_idx].aopen(ctx)) as gen:
                    async for v in gen:
                        yield v
        finally:
            sub.unbind(on_change)
            sub.close()


class ReactForever(Interaction):
    """Execute body on every change (runs forever).

    Children layout: [change, body, changed_key?]
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(
        self,
        change: ChangeOp,
        body: Nu,
        *,
        changed_key: StrArg | None = None,
    ) -> None:
        self._has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, changed_key)
        else:
            super().__init__(change, body)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()

        def on_change(changed_key: object) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, changed_key)

        changed_key_name: str | None = None
        if self._has_changed_key:
            changed_key_name = await self.children[2].afirst(ctx)

        sub = await self.children[0].afirst(ctx)
        sub.bind(on_change)
        try:
            while True:
                key = await queue.get()

                if changed_key_name is not None:
                    ctx.attrs[changed_key_name] = key

                # TODO task-079: redesign changed_key smuggling. For now,
                # body is executed (drained), not streamed, to preserve
                # legolas ledger app semantics.
                await self.children[1].aexecute(ctx)
                if False:
                    yield  # mark as async generator
        finally:
            sub.unbind(on_change)
            sub.close()


class ReactWhile(Interaction):
    """Execute body on each change while condition is truthy.

    Children layout: [change, condition, body, changed_key?]
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(
        self,
        change: ChangeOp,
        condition: Any,
        body: Nu,
        *,
        changed_key: StrArg | None = None,
    ) -> None:
        self._has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, condition, body, changed_key)
        else:
            super().__init__(change, condition, body)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()

        def on_change(changed_key: object) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, changed_key)

        changed_key_name: str | None = None
        if self._has_changed_key:
            changed_key_name = await self.children[3].afirst(ctx)

        sub = await self.children[0].afirst(ctx)
        sub.bind(on_change)
        try:
            while True:
                key = await queue.get()

                if not await self.children[1].afirst(ctx):
                    break

                if changed_key_name is not None:
                    ctx.attrs[changed_key_name] = key

                async with aclosing(self.children[2].aopen(ctx)) as gen:
                    async for v in gen:
                        yield v
        finally:
            sub.unbind(on_change)
            sub.close()
