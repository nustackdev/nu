"""JQueueRef: janus-backed queue ref in the nu-mem fabric.

A leaf ref: occupies a slot in a Shape, holds metadata (capacity,
item_type), and on first fetch vivifies a ``janus.Queue`` at the slot's
path in the backing dict. Subsequent fetches return the same live queue.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import janus

from nu.domains.shape import Slot

from ..base import RefBase
from .form import JQueue


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.domains.shape import Shape
    from nu.lang.runtime import Runtime


__all__ = ["JQueueRef"]


class JQueueRef[T](RefBase[janus.Queue[T]], JQueue[T]):
    """Leaf ref to a janus.Queue stored at a slot in nu-mem state.

    Vivifies the queue on first fetch, then returns the same instance.
    The held item type is metadata only; janus.Queue does not enforce
    element types at runtime.
    """

    def __init__(
        self,
        address: str | int | Nu,
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
        """Declare a JQueueRef slot in a Shape with optional capacity/type."""
        return Slot(cls, capacity=capacity, item_type=item_type)  # type: ignore[return-value]
