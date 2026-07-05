"""Interactions for JQueueRef / JQueueForm.

- Put   — Command, blocks when full → back-pressure.
- Get   — ScalarAction, blocks when empty, yields one item (mutating producer).
- QSize — ScalarQuery, snapshot count.
- Close — Command, shuts down both halves.

Get mutates the underlying janus.Queue while yielding the popped item, so in v2
it is a ScalarAction (effect + yield) rather than a ScalarQuery, and declares
``mutates`` on slot 0. QSize is a pure read: the queue ref in its read slot
yields READ automatically, so it needs no ``mutates``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import janus

from nu import Command, ScalarAction, ScalarQuery
from nu.engine.structure import Declared


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .form import JQueueForm


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
    """Raised by Get when shut down and empty, or by Put when shut down."""


def _normalize_shutdown(exc: BaseException) -> QueueClosed:
    return QueueClosed(str(exc) or "queue is closed")


class Put(Command):
    """Put a value into a JQueueRef. Blocks when full → back-pressure.

    Children: ``[queue, value]``.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, queue: JQueueForm, value: object) -> None:
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
    """Pop one value from a JQueueRef. Blocks when empty.

    Children: ``[queue]``. Yields the popped item. A mutating producer: it
    consumes from the underlying queue and yields, so it is a ScalarAction and
    declares ``mutates`` on slot 0.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, queue: JQueueForm) -> None:
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
    """Snapshot count of items in a JQueueRef.

    Children: ``[queue]``. Yields an int.
    """

    def __init__(self, queue: JQueueForm) -> None:
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
    """Shut down a JQueueRef.

    Subsequent puts raise; pending and subsequent gets drain remaining
    items, then raise QueueClosed.

    Children: ``[queue]``.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, queue: JQueueForm) -> None:
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
