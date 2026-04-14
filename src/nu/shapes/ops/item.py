# ruff: noqa: D102
"""Item access ops - CRUD for items within collections.

ItemLoadOp: Read item value - ref.execute() -> value
ItemStoreCmd: Write item value - parent[address] = value
ItemEraseCmd: Delete item - del parent[address]
ItemExistsOp: Check if item exists - not is_sentinel(ref.execute())
ItemMissingOp: Check if item is missing - is_sentinel(ref.execute())

READ ops delegate to children[0].execute() (goes through Snapshot wrapper).
WRITE ops use children[0] as Ref directly (inside Transaction wrapper).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.terms import EMPTY, Op, Sentinel
from nu.terms.effect import Direction
from nu.terms.sentinel import is_sentinel


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
    """Read item from collection. Returns EMPTY if missing."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> T | Sentinel:
        return await self.children[0].execute(ctx)

    def __repr__(self) -> str:
        return f"ItemLoadOp({self.children[0]!r})"


class ItemStoreCmd[T](Op[None]):
    """Write item to collection: parent[address] = value."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: Ref, value: Nu[T | Sentinel]) -> None:
        super().__init__(ref, value)

    async def execute(self, ctx: Context) -> None:
        ref = self.children[0]
        parent = await ref.fetch_parent(ctx)
        address = await ref.resolve_address(ctx)
        value = await self.children[1].execute(ctx)
        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent[address] = value

    def __repr__(self) -> str:
        return f"ItemStoreCmd({self.children[0]!r}, {self.children[1]!r})"


class ItemEraseCmd(Op[None]):
    """Delete item from collection: del parent[address]."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> None:
        ref = self.children[0]
        parent = await ref.fetch_parent(ctx)
        address = await ref.resolve_address(ctx)
        del parent[address]

    def __repr__(self) -> str:
        return f"ItemEraseCmd({self.children[0]!r})"


class ItemExistsOp(Op[bool]):
    """Check if item exists: not is_sentinel(ref.execute())."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> bool:
        val = await self.children[0].execute(ctx)
        return not is_sentinel(val)

    def __repr__(self) -> str:
        return f"ItemExistsOp({self.children[0]!r})"


class ItemMissingOp(Op[bool]):
    """Check if item is missing: is_sentinel(ref.execute())."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> bool:
        val = await self.children[0].execute(ctx)
        return is_sentinel(val)

    def __repr__(self) -> str:
        return f"ItemMissingOp({self.children[0]!r})"
