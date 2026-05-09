"""JQueueRef — janus-backed queue ref in the nu-mem fabric.

A leaf ref: occupies a slot in a Shape, holds metadata (capacity,
item_type), and on first fetch vivifies a ``janus.Queue`` at the slot's
path in the backing dict. Subsequent fetches return the same live queue.
"""

# ruff: noqa: D102

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Self

import janus

from nu.shapes import Slot
from nu.terms import Mode

from ..base import RefBase
from .form import JQueueForm


if TYPE_CHECKING:
    from nu import Context, Nu
    from nu.shapes import Shape


__all__ = ["JQueueRef"]


class JQueueRef[T](RefBase[janus.Queue[T]], JQueueForm[T]):
    """Leaf ref to a janus.Queue stored at a slot in nu-mem state.

    Vivifies the queue on first fetch, then returns the same instance.
    The held item type is metadata only — janus.Queue does not enforce
    element types at runtime.
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | int | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
        capacity: int | None = None,
        item_type: type[T] = object,  # type: ignore[assignment]
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)
        self._capacity = capacity
        self._item_type = item_type

    def result(self, op: Nu) -> JQueueForm[T]:
        return JQueueForm(op)

    def fetch(self, ctx: Context) -> janus.Queue[T]:
        parent = self.fetch_parent(ctx)
        address = self.resolve_address(ctx)
        if not isinstance(parent, dict):
            msg = f"JQueueRef parent must be a dict, got {type(parent).__name__}"
            raise TypeError(msg)
        q = parent.get(address)
        if q is None:
            q = janus.Queue(maxsize=self._capacity or 0)
            parent[address] = q
        return q

    async def afetch(self, ctx: Context) -> janus.Queue[T]:
        parent = await self.afetch_parent(ctx)
        address = await self.aresolve_address(ctx)
        if not isinstance(parent, dict):
            msg = f"JQueueRef parent must be a dict, got {type(parent).__name__}"
            raise TypeError(msg)
        q = parent.get(address)
        if q is None:
            q = janus.Queue(maxsize=self._capacity or 0)
            parent[address] = q
        return q

    def eval(self, ctx: Context) -> janus.Queue[T]:
        return self.fetch(ctx)

    async def aeval(self, ctx: Context) -> janus.Queue[T]:
        return await self.afetch(ctx)

    @classmethod
    def slot(
        cls,
        *,
        capacity: int | None = None,
        item_type: type = object,
    ) -> Self:
        return Slot(cls, capacity=capacity, item_type=item_type)  # type: ignore[return-value]

    def __repr__(self) -> str:
        cap = "inf" if self._capacity is None else self._capacity
        return f"JQueueRef(item_type={self._item_type.__name__}, capacity={cap})"
