"""Interactions for JQueueRef / JQueue.

- Put: Command, blocks when full for back-pressure.
- Get: ScalarAction, blocks when empty, yields one item (mutating producer).
- QSize: ScalarQuery, snapshot count.
- Close: Command, shuts down both halves.

Get mutates the underlying janus.Queue while yielding the popped item, so it
is a ScalarAction (effect + yield) rather than a ScalarQuery, and declares
``mutates`` on slot 0. QSize is a pure read: the queue ref in its read slot
yields READ automatically, so it needs no ``mutates``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import janus

from nu.engine.structure import Declared
from nu.lang import Command, ScalarAction, ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .form import JQueue


__all__ = [
    "Close",
    "Get",
    "Put",
    "QSize",
    "QueueClosed",
]


_SHUTDOWN_EXCS: tuple[type[BaseException], ...] = (
    janus.ShutDown,
    janus.SyncQueueShutDown,
    janus.AsyncQueueShutDown,
    janus.QueueShutDown,
)


class QueueClosed(Exception):  # noqa: N818
    """Raised when the queue is shut down: by Put always, by Get once drained.

    Notes:
        - One exception for both halves: janus raises a different shutdown
          type per side and per mode, and all of them are normalised to this
          so a consumer catches one thing.
    """


def _normalize_shutdown(exc: BaseException) -> QueueClosed:
    return QueueClosed(str(exc) or "queue is closed")


class Put(Command):
    """Enqueues a value, waiting for room when the queue is full.

    Args:
        queue: the node yielding the queue to write into.
        value: what to enqueue.

    Notes:
        - Waiting is the point: a bounded queue turns a fast producer into a
          slow one instead of letting the backlog grow.
        - Routes itself by mode - the sync run blocks the calling thread, the
          async run awaits on the event loop - so the same tree works from
          either side.
        - A shut-down queue raises QueueClosed rather than dropping the
          value.

    Yields:
        Nothing.

    Example:
        >>> from nu.mem.refs.jqueue import JQueueRef
        >>> class Buf(nu.Shape):
        ...     queue = JQueueRef.slot(capacity=2, item_type=int)
        >>> ctx = nu.Context().bind(dict, {}, Buf)
        >>> _ = nu.run(Buf.queue.put(1), ctx)
        >>> nu.run(Buf.queue.qsize(), ctx)[0]
        1
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, queue: JQueue, value: object) -> None:
        super().__init__(queue, value)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync put thunk."""

        def thunk(rt: Runtime) -> None:
            q = children[0](rt)
            value = children[1](rt)
            try:
                q.sync_q.put(value)
            except _SHUTDOWN_EXCS as e:
                raise _normalize_shutdown(e) from e

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async put thunk."""

        async def athunk(rt: Runtime) -> None:
            q = await children[0](rt)
            value = await children[1](rt)
            try:
                await q.async_q.put(value)
            except _SHUTDOWN_EXCS as e:
                raise _normalize_shutdown(e) from e

        return athunk


class Get(ScalarAction):
    """Takes the oldest item, waiting for one when the queue is empty.

    Args:
        queue: the node yielding the queue to read from.

    Notes:
        - It both consumes and yields, which is why it is an action rather
          than a query: evaluating it twice takes two items, so it is not
          something to treat as a repeatable read.
        - Routes itself by mode - the sync run blocks the calling thread, the
          async run awaits on the event loop.
        - Once the queue is shut down and drained it raises QueueClosed,
          including for a consumer already waiting when the shutdown lands.

    Yields:
        The item taken from the queue.

    Example:
        >>> from nu.mem.refs.jqueue import JQueueRef
        >>> class Buf(nu.Shape):
        ...     queue = JQueueRef.slot(capacity=2, item_type=int)
        >>> ctx = nu.Context().bind(dict, {}, Buf)
        >>> _ = nu.run(Buf.queue.put(7), ctx)
        >>> nu.run(Buf.queue.get(), ctx)[0]
        7
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, queue: JQueue) -> None:
        super().__init__(queue)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync get thunk."""

        def thunk(rt: Runtime) -> object:
            q = children[0](rt)
            try:
                return q.sync_q.get()
            except _SHUTDOWN_EXCS as e:
                raise _normalize_shutdown(e) from e

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async get thunk."""

        async def athunk(rt: Runtime) -> object:
            q = await children[0](rt)
            try:
                return await q.async_q.get()
            except _SHUTDOWN_EXCS as e:
                raise _normalize_shutdown(e) from e

        return athunk


class QSize(ScalarQuery):
    """How many items are waiting in the queue at this instant.

    Args:
        queue: the node yielding the queue to count.

    Notes:
        - A snapshot, not a guarantee: another thread or task can add or take
          an item before the value is used, so it says nothing about whether
          the next ``get`` will wait.
        - A pure read - it never touches the queue's contents - so the only
          fabric effect in the tree is the ref that fetches the queue.

    Yields:
        The item count as an int.

    Example:
        >>> from nu.mem.refs.jqueue import JQueueRef
        >>> class Buf(nu.Shape):
        ...     queue = JQueueRef.slot(item_type=int)
        >>> ctx = nu.Context().bind(dict, {}, Buf)
        >>> nu.run(Buf.queue.qsize(), ctx)[0]
        0
    """

    def __init__(self, queue: JQueue) -> None:
        super().__init__(queue)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync qsize thunk."""

        def thunk(rt: Runtime) -> int:
            q = children[0](rt)
            return q.sync_q.qsize()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async qsize thunk."""

        async def athunk(rt: Runtime) -> int:
            q = await children[0](rt)
            return q.async_q.qsize()

        return athunk


class Close(Command):
    """Shuts the queue down, both the sync and the async half at once.

    Args:
        queue: the node yielding the queue to shut down.

    Notes:
        - Items already queued are not thrown away: consumers drain what is
          left and only then start raising QueueClosed.
        - Any later ``put`` raises QueueClosed; there is no reopening.
        - The slot still holds the same queue object afterwards, so a read
          does not hand back a fresh one.

    Yields:
        Nothing.

    Example:
        >>> from nu.mem.refs.jqueue import JQueueRef, QueueClosed
        >>> class Buf(nu.Shape):
        ...     queue = JQueueRef.slot(item_type=int)
        >>> ctx = nu.Context().bind(dict, {}, Buf)
        >>> _ = nu.run(Buf.queue.close(), ctx)
        >>> try:
        ...     _ = nu.run(Buf.queue.put(1), ctx)
        ... except QueueClosed:
        ...     print("closed")
        closed
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, queue: JQueue) -> None:
        super().__init__(queue)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync close thunk."""

        def thunk(rt: Runtime) -> None:
            q = children[0](rt)
            q.shutdown()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async close thunk."""

        async def athunk(rt: Runtime) -> None:
            q = await children[0](rt)
            q.shutdown()

        return athunk
