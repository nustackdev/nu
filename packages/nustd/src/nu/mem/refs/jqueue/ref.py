"""JQueueRef: janus-backed queue ref in the nu-mem fabric.

A leaf ref: occupies a slot in a Shape, holds metadata (capacity,
item_type), and on first fetch vivifies a ``janus.Queue`` at the slot's
path in the backing dict. Subsequent fetches return the same live queue.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

import janus
from typing_extensions import Self

from nu.domains.shape import Slot

from ..base import RefBase
from .form import JQueue


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape import Shape
    from nu.lang import IntArg, Nu, StrArg
    from nu.lang.runtime import Runtime


__all__ = ["JQueueRef"]


T = TypeVar("T")


class JQueueRef(RefBase[janus.Queue[T]], JQueue[T], Generic[T]):
    """A slot holding a live janus queue, bridging the loop and the threads.

    Reading it hands back the queue object itself rather than any stored
    data, which is what makes one side able to ``put`` from a thread while
    the other ``get``s on the event loop. The queue is created the first time
    the slot is read and kept there, so every later read in the same backing
    dict is the same queue.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Capacity and item type come from the slot declaration; no capacity
          means unbounded, and the item type is metadata that nothing checks
          against what is actually put in.
        - The queue lives in the backing dict like any other value, so it is
          not JSON-shaped and does not survive being serialised.
        - Vivification needs a real dict at the parent path; a non-dict there
          raises TypeError rather than yielding a sentinel.
        - Because reading vivifies, a plain read is enough to create the
          queue before any producer starts.

    Yields:
        The live ``janus.Queue`` at this slot, created on first read.

    Example:
        >>> from nu.mem.refs.jqueue import JQueueRef
        >>> class Buf(nu.Shape):
        ...     queue = JQueueRef.slot(capacity=2, item_type=int)
        >>> ctx = nu.Context().bind(dict, {}, Buf)
        >>> _ = nu.run(Buf.queue.put(1), ctx)
        >>> nu.run(Buf.queue.get(), ctx)[0]
        1
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
        capacity: int | None = None,
        item_type: type[T] = object,  # type: ignore[assignment]
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["capacity"] = capacity
        self._payload["item_type"] = item_type

    @property
    def _capacity(self) -> int | None:
        return self._payload.get("capacity")  # type: ignore[return-value]

    @property
    def _item_type(self) -> type:
        return self._payload.get("item_type", object)  # type: ignore[return-value]

    def _wrap_result(self, op: Nu) -> JQueue[T]:
        """Wrap an interaction node in the typed JQueue surface."""
        return JQueue(op)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync read thunk that vivifies and yields the queue."""
        address = children[1]

        def thunk(rt: Runtime) -> janus.Queue[T]:
            parent = self._fetch_parent(rt)
            if not isinstance(parent, dict):
                msg = f"JQueueRef parent must be a dict, got {type(parent).__name__}"
                raise TypeError(msg)
            addr = address(rt)
            q = parent.get(addr)
            if q is None:
                q = janus.Queue(maxsize=self._capacity or 0)
                parent[addr] = q
            return q

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async read thunk that vivifies and yields the queue."""
        address = children[1]

        async def athunk(rt: Runtime) -> janus.Queue[T]:
            parent = self._fetch_parent(rt)
            if not isinstance(parent, dict):
                msg = f"JQueueRef parent must be a dict, got {type(parent).__name__}"
                raise TypeError(msg)
            addr = await address(rt)
            q = parent.get(addr)
            if q is None:
                q = janus.Queue(maxsize=self._capacity or 0)
                parent[addr] = q
            return q

        return athunk

    @classmethod
    def slot(
        cls,
        *,
        capacity: int | None = None,
        item_type: type = object,
    ) -> Self:
        """Declare a queue slot in a Shape class body.

        Args:
            capacity: how many items may wait before ``put`` blocks.
                Unbounded when absent.
            item_type: the Python type the queue is meant to carry.

        Notes:
            - Both are recorded on the slot and applied when the queue is
              first created; changing them afterwards has no effect on a
              queue already vivified in a backing dict.

        Example:
            class Buf(Shape):
                queue = JQueueRef.slot(capacity=16, item_type=int)
        """
        return Slot(cls, capacity=capacity, item_type=item_type)  # type: ignore[return-value]
