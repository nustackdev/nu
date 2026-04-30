"""Reactive control flows — React, ReactForever, ReactWhile.

Subscribe to change events and execute children in response. Uses Change
queries from shapes.queries to obtain subscription handles, bridges
callback notifications into async via asyncio.Queue (one wake per
notification, no collapsing).
"""

from __future__ import annotations

import asyncio
from contextlib import aclosing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Control
from nu.terms.nu import NuBase
from nu.terms.types import Mode

from ..queries.reactive import Change  # noqa: TC001 - runtime dependency


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu import Context, Nu
    from nu.terms import StrArg


__all__ = [
    "React",
    "ReactForever",
    "ReactWhile",
]


class React(NuBase):
    """Wait for a single change, then execute body once.

    Children layout: [change, body?, changed_key?]
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(
        self,
        change: Change,
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
        from nu import runtime

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()

        def on_change(changed_key: object) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, changed_key)

        changed_key_name: str | None = None
        if self._changed_key_idx is not None:
            changed_key_name = await runtime.afirst(
                self._children[self._changed_key_idx],
                ctx,
            )

        sub = await runtime.afirst(self._children[0], ctx)
        sub.bind(on_change)
        try:
            key = await queue.get()

            if changed_key_name is not None:
                ctx.attrs[changed_key_name] = key

            if self._body_idx is not None:
                async with aclosing(self._children[self._body_idx].aopen(ctx)) as gen:
                    async for v in gen:
                        yield v
        finally:
            sub.unbind(on_change)
            sub.close()


class ReactForever(Control):
    """Execute body on every change (runs forever).

    Children layout: [change, body, changed_key?]
    """

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(
        self,
        change: Change,
        body: Nu,
        *,
        changed_key: StrArg | None = None,
    ) -> None:
        self._has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, changed_key)
        else:
            super().__init__(change, body)

    def run(self, ctx: Context) -> None:
        msg = "ReactForever requires async runtime"
        raise NotImplementedError(msg)

    async def arun(self, ctx: Context) -> None:
        from nu import runtime

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()

        def on_change(changed_key: object) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, changed_key)

        changed_key_name: str | None = None
        if self._has_changed_key:
            changed_key_name = await runtime.afirst(self._children[2], ctx)

        sub = await runtime.afirst(self._children[0], ctx)
        sub.bind(on_change)
        try:
            while True:
                key = await queue.get()

                if changed_key_name is not None:
                    ctx.attrs[changed_key_name] = key

                # TODO task-079: redesign changed_key smuggling. For now,
                # body is executed (drained), not streamed, to preserve
                # legolas ledger app semantics.
                await runtime.aexecute(self._children[1], ctx)
        finally:
            sub.unbind(on_change)
            sub.close()


class ReactWhile(NuBase):
    """Execute body on each change while condition is truthy.

    Children layout: [change, condition, body, changed_key?]
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(
        self,
        change: Change,
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
        from nu import runtime

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()

        def on_change(changed_key: object) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, changed_key)

        changed_key_name: str | None = None
        if self._has_changed_key:
            changed_key_name = await runtime.afirst(self._children[3], ctx)

        sub = await runtime.afirst(self._children[0], ctx)
        sub.bind(on_change)
        try:
            while True:
                key = await queue.get()

                if not await runtime.afirst(self._children[1], ctx):
                    break

                if changed_key_name is not None:
                    ctx.attrs[changed_key_name] = key

                async with aclosing(self._children[2].aopen(ctx)) as gen:
                    async for v in gen:
                        yield v
        finally:
            sub.unbind(on_change)
            sub.close()
