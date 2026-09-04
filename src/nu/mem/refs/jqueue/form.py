"""JQueue: typed surface for janus-backed queue refs.

Pure TypedNu wrapper. Holds no state; methods build interaction trees
against the wrapped Nu (typically a JQueueRef).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

import janus

from nu.forms import Form, TypedNu


if TYPE_CHECKING:
    from .interactions import Close, Get, Put, QSize


__all__ = ["JQueue"]


T = TypeVar("T")


class JQueue(Form, TypedNu[janus.Queue[T]], Generic[T]):
    """The queue verbs, over any node that yields a janus queue.

    Holds nothing itself: it wraps one Nu child, normally a ``JQueueRef``,
    and every call on it builds an interaction over that child. A ref that
    reads a queue therefore gets ``put``, ``get``, ``qsize`` and ``close``
    just by mixing this in.

    Args:
        operand: the node yielding the queue to act on.

    Notes:
        - The calls do not touch the queue: they build a tree, and nothing
          happens until it runs.

    Yields:
        Whatever the wrapped child yields, unchanged; the surface adds calls,
        not a value of its own.

    Example:
        >>> from nu.mem.refs.jqueue import JQueueRef
        >>> class Buf(nu.Shape):
        ...     queue = JQueueRef.slot(item_type=int)
        >>> ctx = nu.Context().bind(dict, {}, Buf)
        >>> _ = nu.run(Buf.queue.put(7), ctx)
        >>> nu.run(Buf.queue.qsize(), ctx)[0]
        1
    """

    def put(self, value: object) -> Put:
        """Enqueue ``value``, waiting for room when the queue is full.

        Notes:
            - Blocking is the back-pressure: a bounded queue makes the
              producer wait rather than growing without limit.
            - Raises QueueClosed when the queue is already shut down.

        Example:
            run(Buf.queue.put(1), ctx)
        """
        from .interactions import Put

        return Put(self, value)

    def get(self) -> Get:
        """Take the oldest item, waiting for one when the queue is empty.

        Notes:
            - This both mutates the queue and yields, so it is an action,
              not a read; it cannot be treated as a pure query.
            - Raises QueueClosed once the queue is shut down and drained.

        Example:
            run(Buf.queue.get(), ctx)
        """
        from .interactions import Get

        return Get(self)

    def qsize(self) -> QSize:
        """Count the items waiting in the queue right now.

        Notes:
            - A snapshot only: a producer or consumer on another thread can
              change it the moment it is read.

        Example:
            run(Buf.queue.qsize(), ctx)
        """
        from .interactions import QSize

        return QSize(self)

    def close(self) -> Close:
        """Shut the queue down on both the sync and the async half.

        Notes:
            - Items already queued stay readable; consumers drain them and
              only then start raising QueueClosed.

        Example:
            run(Buf.queue.close(), ctx)
        """
        from .interactions import Close

        return Close(self)
