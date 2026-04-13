# ruff: noqa: D102
"""Item access ops - CRUD for items within collections.

ItemLoadOp: Read item value - parent[address]
ItemStoreCmd: Write item value - parent[address] = value
ItemEraseCmd: Delete item - del parent[address]
ItemExistsOp: Check if item exists - address in parent
ItemMissingOp: Check if item is missing - address not in parent

These operate via standard Python protocols (__getitem__, __setitem__,
__delitem__, __contains__). The ref provides fetch_parent(ctx) to get
the collection and resolve_address(ctx) to get the key/index.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.terms import EMPTY, Op, Sentinel
from nu.terms.effect import Direction


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


class ItemLoadOp[T](Op[T | Sentinel]):
    """Read item from collection: parent[address].

    Returns EMPTY if the key/index doesn't exist.
    """

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> T | Sentinel:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        try:
            return parent[address]
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"ItemLoadOp({self.ref!r})"


class ItemStoreCmd[T](Op[None]):
    """Write item to collection: parent[address] = value. Returns None."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: Ref, value: Nu[T | Sentinel]) -> None:
        super().__init__(ref, value)
        self.ref = ref
        self.value_expr = value

    async def execute(self, ctx: Context) -> None:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        value = await self.value_expr.execute(ctx)
        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent[address] = value
        return None

    def __repr__(self) -> str:
        return f"ItemStoreCmd({self.ref!r}, {self.value_expr!r})"


class ItemEraseCmd(Op[None]):
    """Delete item from collection: del parent[address]."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> None:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        del parent[address]
        return None

    def __repr__(self) -> str:
        return f"ItemEraseCmd({self.ref!r})"


class ItemExistsOp(Op[bool]):
    """Check if item exists in collection: address in parent."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address in parent

    def __repr__(self) -> str:
        return f"ItemExistsOp({self.ref!r})"


class ItemMissingOp(Op[bool]):
    """Check if item is missing from collection: address not in parent."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address not in parent

    def __repr__(self) -> str:
        return f"ItemMissingOp({self.ref!r})"
