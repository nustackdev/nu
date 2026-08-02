"""JQueue — typed surface for janus-backed queue refs.

Pure TypedNu wrapper. Holds no state; methods build interaction trees
against the wrapped Nu (typically a JQueueRef).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import janus

from nu import Form, TypedNu


if TYPE_CHECKING:
    from .interactions import Close, Get, Put, QSize


__all__ = ["JQueue"]


class JQueue[T](Form, TypedNu[janus.Queue[T]]):
    """Typed surface for a janus.Queue handle.

    Wraps a Nu child (typically a JQueueRef). Method calls produce
    Interaction trees over the wrapped node.
    """

    def put(self, value: object) -> Put:
        """Build a Put interaction enqueuing ``value`` onto this queue."""
        from .interactions import Put

        return Put(self, value)

    def get(self) -> Get:
        """Build a Get interaction popping one item from this queue."""
        from .interactions import Get

        return Get(self)

    def qsize(self) -> QSize:
        """Build a QSize interaction yielding this queue's item count."""
        from .interactions import QSize

        return QSize(self)

    def close(self) -> Close:
        """Build a Close interaction shutting down this queue."""
        from .interactions import Close

        return Close(self)
