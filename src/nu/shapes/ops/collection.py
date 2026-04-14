# ruff: noqa: D102
"""Collection-level ops - get, set, delete, exists, missing.

Same logic as item ops but distinct tree node types, so substrates
can match on CollectionLoadOp vs ItemLoadOp for type-specific deformations
(e.g. PV primitive optimizations only target Item* variants).

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
    "CollectionEraseCmd",
    "CollectionExistsOp",
    "CollectionLoadOp",
    "CollectionMissingOp",
    "CollectionStoreCmd",
]


class CollectionLoadOp[T](Op[T | Sentinel]):
    """Read collection from parent. Returns EMPTY if missing."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> T | Sentinel:
        return await self.children[0].execute(ctx)

    def __repr__(self) -> str:
        return f"CollectionLoadOp({self.children[0]!r})"


class CollectionStoreCmd[T](Op[None]):
    """Write collection to parent: parent[address] = data."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: Ref, data: Nu[T | Sentinel]) -> None:
        super().__init__(ref, data)

    async def execute(self, ctx: Context) -> None:
        data = await self.children[1].execute(ctx)
        if isinstance(data, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {data}")
        ref = self.children[0]
        parent = await ref.fetch_parent(ctx)
        address = await ref.resolve_address(ctx)
        parent[address] = data

    def __repr__(self) -> str:
        return f"CollectionStoreCmd({self.children[0]!r}, {self.children[1]!r})"


class CollectionEraseCmd(Op[None]):
    """Delete collection from parent: del parent[address]."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> None:
        ref = self.children[0]
        parent = await ref.fetch_parent(ctx)
        address = await ref.resolve_address(ctx)
        del parent[address]

    def __repr__(self) -> str:
        return f"CollectionEraseCmd({self.children[0]!r})"


class CollectionExistsOp(Op[bool]):
    """Check if collection exists: not is_sentinel(ref.execute())."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> bool:
        val = await self.children[0].execute(ctx)
        return not is_sentinel(val)

    def __repr__(self) -> str:
        return f"CollectionExistsOp({self.children[0]!r})"


class CollectionMissingOp(Op[bool]):
    """Check if collection is missing: is_sentinel(ref.execute())."""

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> bool:
        val = await self.children[0].execute(ctx)
        return is_sentinel(val)

    def __repr__(self) -> str:
        return f"CollectionMissingOp({self.children[0]!r})"
