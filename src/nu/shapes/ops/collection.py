# ruff: noqa: D102
"""Collection-level ops — get, set, delete, exists, missing.

Same logic as item ops but distinct tree node types, so substrates
can match on CollectionLoadOp vs ItemLoadOp for type-specific deformations
(e.g. PV primitive optimizations only target Item* variants).

All ops use the same parent[address] primitives as item ops.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import EMPTY, Command, Op, Calculation, Sentinel


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = [
    "CollectionEraseCmd",
    "CollectionExistsOp",
    "CollectionLoadOp",
    "CollectionMissingOp",
    "CollectionStoreCmd",
]


class CollectionLoadOp[T](Calculation, Op[T | Sentinel]):
    """Read collection from parent: parent[address]."""

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
        return f"CollectionLoadOp({self.ref!r})"


class CollectionStoreCmd[T](Command, Op[None]):
    """Write collection to parent: parent[address] = data. Returns None."""

    def __init__(self, ref: object, data: Nu[T | Sentinel]) -> None:
        super().__init__(ref, data)
        self.ref = ref
        self.data_expr = data

    async def execute(self, ctx: Context) -> None:
        data = await self.data_expr.execute(ctx)
        if isinstance(data, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {data}")

        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        parent[address] = data
        return None

    def __repr__(self) -> str:
        return f"CollectionStoreCmd({self.ref!r}, {self.data_expr!r})"


class CollectionEraseCmd(Command, Op[None]):
    """Delete collection from parent: del parent[address]."""

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> None:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        del parent[address]
        return None

    def __repr__(self) -> str:
        return f"CollectionEraseCmd({self.ref!r})"


class CollectionExistsOp(Calculation, Op[bool]):
    """Check if collection exists in parent: address in parent."""

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address in parent

    def __repr__(self) -> str:
        return f"CollectionExistsOp({self.ref!r})"


class CollectionMissingOp(Calculation, Op[bool]):
    """Check if collection is missing from parent: address not in parent."""

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address not in parent

    def __repr__(self) -> str:
        return f"CollectionMissingOp({self.ref!r})"
