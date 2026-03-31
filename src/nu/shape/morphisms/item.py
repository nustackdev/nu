# ruff: noqa: D102
"""Item access morphisms — CRUD for items within collections.

ItemLoadOp: Read item value — parent[address]
ItemStoreCmd: Write item value — parent[address] = value
ItemEraseCmd: Delete item — del parent[address]
ItemExistsOp: Check if item exists — address in parent
ItemMissingOp: Check if item is missing — address not in parent

These operate via standard Python protocols (__getitem__, __setitem__,
__delitem__, __contains__). The ref provides fetch_parent(ctx) to get
the collection and resolve_address(ctx) to get the key/index.

Any substrate ref that implements fetch_parent(ctx) and resolve_address(ctx)
can use these morphisms directly.

PV-specific item morphisms (InitCmd, ItemPrimitiveGetOp, ItemPrimitiveSetCmd,
ItemPrimitiveSetUnsafeCmd, ItemPrimitiveDeleteCmd) live in eb_virtuals.morphisms.item.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import EMPTY, Command, Morphism, Operation, Sentinel


if TYPE_CHECKING:
    from nu import Context, Term


__all__ = [
    "ItemEraseCmd",
    "ItemExistsOp",
    "ItemLoadOp",
    "ItemMissingOp",
    "ItemStoreCmd",
]


class ItemLoadOp[T](Operation, Morphism[T | Sentinel]):
    """Read item from collection: parent[address].

    Uses __getitem__ on the parent collection. Returns EMPTY
    if the key/index doesn't exist.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
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


class ItemStoreCmd[T](Command, Morphism[None]):
    """Write item to collection: parent[address] = value. Returns None.

    Uses __setitem__ on the parent collection.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, value: Term[T | Sentinel]) -> None:
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


class ItemEraseCmd(Command, Morphism[None]):
    """Delete item from collection: del parent[address].

    Uses __delitem__ on the parent collection.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> None:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        del parent[address]
        return None

    def __repr__(self) -> str:
        return f"ItemEraseCmd({self.ref!r})"


class ItemExistsOp(Operation, Morphism[bool]):
    """Check if item exists in collection: address in parent.

    Uses __contains__ on the parent collection.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address in parent

    def __repr__(self) -> str:
        return f"ItemExistsOp({self.ref!r})"


class ItemMissingOp(Operation, Morphism[bool]):
    """Check if item is missing from collection: address not in parent.

    Inverse of ItemExistsOp.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address not in parent

    def __repr__(self) -> str:
        return f"ItemMissingOp({self.ref!r})"
