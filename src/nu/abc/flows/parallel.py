"""Parallel flows -- concurrent execution via asyncio."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu import Flow


if TYPE_CHECKING:
    from nu import Context, Executable


__all__ = [
    "All",
    "Any",
    "Parallel",
    "Race",
]


class Parallel(Flow):
    """Execute children concurrently via asyncio.gather.

    All children are launched as async tasks and gathered.
    First exception encountered is propagated.

    Example::

        Parallel(fetch_users, fetch_posts, fetch_comments)
    """

    def __init__(self, *children: Executable) -> None:
        """Initialize parallel flow.

        Args:
            *children: Children to execute concurrently.
        """
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Execute children concurrently via asyncio.gather."""
        if not self.children:
            return

        await asyncio.gather(*(child.execute(ctx) for child in self.children))


class Race(Flow):
    """Execute children concurrently, complete on first finish.

    The first child to complete (success or failure) wins.
    All remaining tasks are cancelled.

    Example::

        Race(fetch_from_primary, fetch_from_replica)
    """

    def __init__(self, *children: Executable) -> None:
        """Initialize race flow.

        Args:
            *children: Children to race concurrently.
        """
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Execute children concurrently, return on first completion."""
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


class All(Flow):
    """Execute children concurrently, fail fast on first exception.

    All children run as concurrent tasks. If any child raises,
    remaining tasks are cancelled and the exception propagates.

    Example::

        All(validate_input, check_permissions, load_config)
    """

    def __init__(self, *children: Executable) -> None:
        """Initialize all flow.

        Args:
            *children: Children to execute concurrently.
        """
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Execute all children concurrently, cancel on first failure."""
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


class Any(Flow):
    """Execute children concurrently, succeed if any one succeeds.

    Children run as concurrent tasks. The first child to succeed
    cancels the rest. If all children fail, the last exception
    is raised.

    Example::

        Any(try_cache, try_database, try_remote_api)
    """

    def __init__(self, *children: Executable) -> None:
        """Initialize any flow.

        Args:
            *children: Children to execute concurrently.
        """
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Execute children concurrently, succeed on first success."""
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
