# ruff: noqa: D102
"""Collection-level ops - get, set, delete, exists, missing.

Same logic as item ops but distinct tree node types, so substrates
can match on CollectionLoadOp vs ItemLoadOp for type-specific deformations
(e.g. PV primitive optimizations only target Item* variants).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.terms import EMPTY, Op, Sentinel
from nu.terms.effect import Direction


if TYPE_CHECKING:
    from nu import Context, Nu

    from nu.shapes.refs import Ref


__all__ = [
    "CollectionEraseCmd",
    "CollectionExistsOp",
    "CollectionLoadOp",
    "CollectionMissingOp",
    "CollectionStoreCmd",
]


class CollectionLoadOp[T](Op[T | Sentinel]):
    """Read collection from parent: parent[address]."""

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
        return f"CollectionLoadOp({self.ref!r})"


class CollectionStoreCmd[T](Op[None]):
    """Write collection to parent: parent[address] = data. Returns None."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: Ref, data: Nu[T | Sentinel]) -> None:
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


class CollectionEraseCmd(Op[None]):
    """Delete collection from parent: del parent[address]."""

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
        return f"CollectionEraseCmd({self.ref!r})"


class CollectionExistsOp(Op[bool]):
    """Check if collection exists in parent: address in parent."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address in parent

    def __repr__(self) -> str:
        return f"CollectionExistsOp({self.ref!r})"


class CollectionMissingOp(Op[bool]):
    """Check if collection is missing from parent: address not in parent."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address not in parent

    def __repr__(self) -> str:
        return f"CollectionMissingOp({self.ref!r})"
