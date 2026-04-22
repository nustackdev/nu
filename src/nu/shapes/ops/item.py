# ruff: noqa: D102
"""Item access ops - CRUD for items within collections.

ItemLoadOp:    Read item value - yields ref's value
ItemStoreCmd:  Write item value - parent[address] = value
ItemEraseCmd:  Delete item - del parent[address]
ItemExistsOp:  Check if item exists
ItemMissingOp: Check if item is missing

READ ops go through ref.aopen (Snapshot wrapper).
WRITE ops use children[0] as Ref directly (inside Transaction wrapper).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.terms import Command, Mode, Query, Sentinel, is_sentinel


if TYPE_CHECKING:
    from nu import Context, Nu
    from nu.shapes.refs import Ref


__all__ = [
    "ItemEraseCmd",
    "ItemExistsOp",
    "ItemLoadOp",
    "ItemMissingOp",
    "ItemStoreCmd",
]


class ItemLoadOp[T](Query[T | Sentinel]):
    """Read item from collection. Returns EMPTY if missing."""

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> T | Sentinel:
        return await self.children[0].afirst(ctx)

    def run(self, ctx: Context) -> T | Sentinel:
        return self.children[0].first(ctx)

    def __repr__(self) -> str:
        return f"ItemLoadOp({self.children[0]!r})"


class ItemStoreCmd[T](Command):
    """Write item to collection: parent[address] = value."""

    writes = 0
    mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, ref: Ref, value: Nu[T | Sentinel]) -> None:
        super().__init__(ref, value)

    async def arun(self, ctx: Context) -> None:
        ref = self.children[0]
        parent = await ref.fetch_parent(ctx)
        address = await ref.resolve_address(ctx)
        value = await self.children[1].afirst(ctx)
        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent[address] = value

    def __repr__(self) -> str:
        return f"ItemStoreCmd({self.children[0]!r}, {self.children[1]!r})"


class ItemEraseCmd(Command):
    """Delete item from collection: del parent[address]."""

    writes = 0
    mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> None:
        ref = self.children[0]
        parent = await ref.fetch_parent(ctx)
        address = await ref.resolve_address(ctx)
        del parent[address]

    def __repr__(self) -> str:
        return f"ItemEraseCmd({self.children[0]!r})"


class ItemExistsOp(Query[bool]):
    """Check if item exists."""

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> bool:
        val = await self.children[0].afirst(ctx)
        return not is_sentinel(val)

    def run(self, ctx: Context) -> bool:
        val = self.children[0].first(ctx)
        return not is_sentinel(val)

    def __repr__(self) -> str:
        return f"ItemExistsOp({self.children[0]!r})"


class ItemMissingOp(Query[bool]):
    """Check if item is missing."""

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> bool:
        val = await self.children[0].afirst(ctx)
        return is_sentinel(val)

    def run(self, ctx: Context) -> bool:
        val = self.children[0].first(ctx)
        return is_sentinel(val)

    def __repr__(self) -> str:
        return f"ItemMissingOp({self.children[0]!r})"
