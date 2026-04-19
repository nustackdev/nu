"""Parallel ops -- Race, All, Any.

(Parallel removed: parallel composition is `a | b` on the Nu base,
building a NuIndepComm. Race/All/Any stay: they are distinct semantics
over concurrent children - first-completed, fail-fast, succeed-if-any.)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from nu.terms import Op


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "All",
    "Any",
    "Race",
]


class Race(Op):
    """Execute children concurrently, complete on first finish.

    Children: ``[*children]``
    """

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover - marks this as an async generator
            yield
        if not self.children:
            return
        tasks = [asyncio.create_task(child.execute(ctx)) for child in self.children]
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


class All(Op):
    """Execute children concurrently, fail fast on first exception.

    Children: ``[*children]``
    """

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover
            yield
        if not self.children:
            return
        tasks = [asyncio.create_task(child.execute(ctx)) for child in self.children]
        try:
            await asyncio.gather(*tasks)
        except Exception:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise


class Any(Op):
    """Execute children concurrently, succeed if any one succeeds.

    Children: ``[*children]``
    """

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        if False:  # pragma: no cover
            yield
        if not self.children:
            return
        tasks = {asyncio.create_task(child.execute(ctx)) for child in self.children}
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
