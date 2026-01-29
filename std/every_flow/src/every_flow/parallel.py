"""Parallel -- concurrent execution via asyncio.gather."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from everyabc import Flow


if TYPE_CHECKING:
    from everyabc import Context, Executable


__all__ = [
    "Parallel",
]


class Parallel(Flow):
    """Execute children concurrently via asyncio.gather.

    All children are launched as async tasks and gathered.
    First exception encountered is propagated.

    Example::

        Parallel(fetch_users, fetch_posts, fetch_comments)
    """

    def __init__(self, *children: Executable, max_workers: int | None = None) -> None:
        """Initialize parallel flow.

        Args:
            *children: Children to execute concurrently.
            max_workers: Max thread pool size (None = default).
        """
        super().__init__(*children)
        self._max_workers = max_workers

    async def execute(self, ctx: Context) -> None:
        """Execute children concurrently via asyncio.gather."""
        if not self.children:
            return

        await asyncio.gather(*(child.execute(ctx) for child in self.children))
