"""JQueueForm — typed surface for janus-backed queue refs.

Pure TypedNu wrapper. Holds no state; methods build interaction trees
against the wrapped Nu (typically a JQueueRef).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import janus

from nu.terms import Form, TypedNu


if TYPE_CHECKING:
    from .interactions import Close, Get, Put, QSize


__all__ = ["JQueueForm"]


class JQueueForm[T](Form, TypedNu[janus.Queue[T]]):
    """Typed surface for a janus.Queue handle.

    Wraps a Nu child (typically a JQueueRef). Method calls produce
    Interaction trees over the wrapped node.
    """

    def put(self, value: object) -> Put:  # noqa: D102
        from .interactions import Put

        return Put(self, value)

    def get(self) -> Get:  # noqa: D102
        from .interactions import Get

        return Get(self)

    def qsize(self) -> QSize:  # noqa: D102
        from .interactions import QSize

        return QSize(self)

    def close(self) -> Close:  # noqa: D102
        from .interactions import Close

        return Close(self)
