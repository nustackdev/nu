"""nustd.queue: a janus queue in a mem slot, the bridge between the loop and the threads.

A bounded FIFO bridging asyncio and threads. Use when one side runs on
the event loop (e.g. fetchers) and the other in a thread (e.g.
processors). ``put`` and ``get`` work in both modes; the underlying
``janus.Queue`` routes each call to the right half. The ref is a ``nu.mem``
ref, so the queue lives in the dict bound for its Shape.

Needs janus, which rides the optional ``nustd[queue]`` extra.

Usage::

    class Buf(nu.Shape):
        queue = nustd.queue.JQueueRef.slot(capacity=16, item_type=int)
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
