"""Per-key serial queues, the engine behind ``ReactEach``.

A ``KeyedQueues`` runs one body per notification, in order within a key and
side by side across keys. Each key that has work gets a backlog of its
pending notifications and one worker that pops them off one at a time; a
worker ends the moment its backlog is empty, so a key seen once and never
again holds nothing afterwards. The next notification for that key simply
starts a fresh worker.

The workers are arms of an ``ArmBook`` (``nu.core.reactive._arms``), keyed
by notification key: the book keeps them, notices the first one to raise,
and drains them on the way out. What this module adds is the backlog per
key and the worker that runs it down. The engine knows nothing of runtimes
or bodies: it is handed a ``run`` coroutine function that runs the body once
for one key, and that is all it ever calls.
"""

from __future__ import annotations

import asyncio
from collections import deque
from typing import TYPE_CHECKING

from .._arms import ArmBook, hashable


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

__all__ = ["KeyedQueues"]


class KeyedQueues:
    """One serial queue per key, each with a worker that lives while it has work.

    Args:
        run: runs the body once for one notification key; awaited by that
            key's worker, one notification at a time.
        owner: the flow's name, for error messages.

    Notes:
        - Keys must be hashable: the backlogs and the book are dicts keyed
          by them. A key that is not raises ``TypeError`` naming the owner.
          A ``None`` key is a key like any other.
        - Memory is bounded by the backlog, as ``ReactEvery``'s queue is: a
          key notified faster than its body runs piles up notifications.
        - The first worker to raise is kept by the book: ``wait`` and ``put``
          raise it, and nothing is started after it.
        - Not thread safe: every call runs on the flow's event loop.
    """

    def __init__(
        self, run: Callable[[object], Awaitable[None]], *, owner: str = "KeyedQueues"
    ) -> None:
        self._run = run
        self._owner = owner
        self.backlogs: dict[object, deque] = {}
        self.book = ArmBook(self._start, owner=owner)

    async def wait(self, aw: Awaitable) -> object:
        """Await ``aw``, unless a worker raises first: then its error is raised here instead."""
        return await self.book.wait(aw)

    async def put(self, key: object) -> None:
        """Queue one notification for ``key``, starting its worker if it has none.

        Raises:
            TypeError: a key that is not hashable.
            The first worker error, if any worker has raised.
        """
        hashable(self._owner, key)
        backlog = self.backlogs.get(key)
        if backlog is not None:
            backlog.append(key)
            return
        self.backlogs[key] = deque([key])
        # No worker runs for a key without a backlog, so this is a birth.
        await self.book.restart(key)

    async def drain(self) -> None:
        """Cancel every live worker, drop every backlog, and wait for each to unwind."""
        self.backlogs.clear()
        await self.book.drain()

    def _start(self, key: object) -> asyncio.Task:
        return asyncio.ensure_future(self._work(key))

    async def _work(self, key: object) -> None:
        """Run the body for every notification in ``key``'s backlog, then leave."""
        backlog = self.backlogs[key]
        try:
            while backlog:
                await self._run(backlog.popleft())
        finally:
            # The empty check and this removal run on one tick, so a
            # notification can never land between a worker deciding it is
            # done and its backlog going away. Only this worker's own backlog
            # goes: one put there since belongs to the worker that follows.
            if self.backlogs.get(key) is backlog:
                del self.backlogs[key]
