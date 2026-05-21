"""Budget - per-execution resources: thread pool, async semaphore, gate.

A Runtime owns a Budget for the lifetime of one entry call. ``max_parallel``
is the tree-wide gate: ``1`` means no concurrency, parallel helpers fall
through to sequential; ``> 1`` allocates a bounded ThreadPoolExecutor and,
in async mode, an asyncio.Semaphore.

Construction is cheap when ``max_parallel == 1`` (no pool, no semaphore).
Close is idempotent and shuts down the pool with ``wait=False`` so cancelled
work doesn't block the caller.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from types import TracebackType

__all__ = ["Budget"]


class Budget:
    """Per-execution thread pool and concurrency gate.

    ``max_parallel == 1`` is the zero-concurrency case: no pool, no semaphore,
    every parallel helper sequentializes. ``> 1`` allocates a bounded
    ThreadPoolExecutor; the async-mode variant also allocates an
    ``asyncio.Semaphore`` for gating ``aeval_parallel`` and friends.
    """

    __slots__ = ("async_mode", "async_sem", "max_parallel", "thread_pool")

    def __init__(self, max_parallel: int = 1, *, async_mode: bool = False) -> None:
        if max_parallel < 1:
            msg = f"max_parallel must be >= 1, got {max_parallel}"
            raise ValueError(msg)
        self.max_parallel = max_parallel
        self.async_mode = async_mode
        self.thread_pool: ThreadPoolExecutor | None = None
        self.async_sem: asyncio.Semaphore | None = None
        if max_parallel > 1:
            self.thread_pool = ThreadPoolExecutor(
                max_workers=max_parallel,
                thread_name_prefix="nu2-worker",
            )
            if async_mode:
                self.async_sem = asyncio.Semaphore(max_parallel)

    def close(self) -> None:
        """Shut down the thread pool. Idempotent."""
        if self.thread_pool is not None:
            self.thread_pool.shutdown(wait=False, cancel_futures=True)
            self.thread_pool = None

    def __enter__(self) -> Budget:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Budget(max_parallel={self.max_parallel}, async_mode={self.async_mode})"
