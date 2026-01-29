"""Parallel -- concurrent execution via ThreadPoolExecutor."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from everyabc import Flow


if TYPE_CHECKING:
    from everyabc import Context, Exec


__all__ = [
    "Parallel",
]


class Parallel(Flow):
    """Execute children concurrently via ThreadPoolExecutor.

    All children are submitted to a thread pool and waited on.
    First exception encountered is propagated.

    Example::

        Parallel(fetch_users, fetch_posts, fetch_comments)
    """

    __slots__ = ("_max_workers",)

    def __init__(self, *children: Exec, max_workers: int | None = None) -> None:
        """Initialize parallel flow.

        Args:
            *children: Children to execute concurrently.
            max_workers: Max thread pool size (None = default).
        """
        super().__init__(*children)
        self._max_workers = max_workers

    def execute(self, ctx: Context) -> None:
        """Execute children in parallel threads."""
        if not self.children:
            return

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {pool.submit(child.execute, ctx): child for child in self.children}
            for future in as_completed(futures):
                future.result()
