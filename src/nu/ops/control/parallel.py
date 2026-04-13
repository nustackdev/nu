"""Parallel ops -- concurrent execution via asyncio."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.terms import Op


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "All",
    "Any",
    "Parallel",
    "Race",
]


class Parallel(Op):
    """Execute children concurrently via asyncio.gather.

    Children: ``[*children]``
    """

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        if not self.children:
            return
        await asyncio.gather(*(child.execute(ctx) for child in self.children))


class Race(Op):
    """Execute children concurrently, complete on first finish.

    Children: ``[*children]``
    """

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
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
                    raise task.exception()
        except:
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

    async def execute(self, ctx: Context) -> None:
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

    async def execute(self, ctx: Context) -> None:
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
                    last_error = exc
            if last_error is not None:
                raise last_error
        except:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            raise
