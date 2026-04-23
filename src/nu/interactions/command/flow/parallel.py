"""Parallel ops -- Race, ParAll, ParAny.

(Parallel removed: parallel composition is `a | b` on the Nu base,
building a NuIndepComm. Race/ParAll/ParAny stay: they are distinct semantics
over concurrent children - first-completed, fail-fast, succeed-if-any.)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms import Flow, Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "ParAll",
    "ParAny",
    "Race",
]


class Race(Flow):
    """Execute children concurrently, complete on first finish.

    Children: ``[*children]``
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover - marks this as an async generator
            yield
        if not self.children:
            return
        tasks = [asyncio.create_task(child.aexecute(ctx)) for child in self.children]
        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                if task.exception() is not None:
                    raise task.exception()  # type: ignore[misc]
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise


class ParAll(Flow):
    """Execute children concurrently, fail fast on first exception.

    Children: ``[*children]``
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover
            yield
        if not self.children:
            return
        tasks = [asyncio.create_task(child.aexecute(ctx)) for child in self.children]
        try:
            await asyncio.gather(*tasks)
        except Exception:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise


class ParAny(Flow):
    """Execute children concurrently, succeed if any one succeeds.

    Children: ``[*children]``
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover
            yield
        if not self.children:
            return
        tasks = {asyncio.create_task(child.aexecute(ctx)) for child in self.children}
        last_error: Exception | None = None
        try:
            while tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    exc = task.exception()
                    if exc is None:
                        for t in tasks:
                            t.cancel()
                        if tasks:
                            await asyncio.gather(*tasks, return_exceptions=True)
                        return
                    last_error = exc  # type: ignore[assignment]
            if last_error is not None:
                raise last_error
        except BaseException:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            raise
