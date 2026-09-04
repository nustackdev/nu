"""Janus-backed queue ref for the nu-mem fabric.

A bounded FIFO bridging asyncio and threads. Use when one side runs on
the event loop (e.g. fetchers) and the other in a thread (e.g.
processors). ``put`` and ``get`` work in both modes; the underlying
``janus.Queue`` routes each call to the right half.

Needs janus, which rides the optional ``nustd[mem]`` extra.

Not re-exported from ``nu.mem`` (the janus import is optional), so reach for
it by its own path.

Usage::

    from nu.mem.refs.jqueue import JQueueRef
    from nu.domains.shape import Shape

    class Buf(Shape):
        queue = JQueueRef.slot(capacity=16, item_type=int)
"""

from .form import JQueue
from .interactions import Close, Get, Put, QSize, QueueClosed
from .ref import JQueueRef


__all__ = [
    "Close",
    "Get",
    "JQueue",
    "JQueueRef",
    "Put",
    "QSize",
    "QueueClosed",
]
