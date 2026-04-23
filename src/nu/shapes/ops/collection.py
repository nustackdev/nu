# ruff: noqa: D102
"""Collection-level ops - get, set, delete, exists, missing.

Same logic as item ops but distinct tree node types, so substrates
can match on CollectionLoadOp vs ItemLoadOp for type-specific deformations
(e.g. PV primitive optimizations only target Item* variants).

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
    "CollectionEraseCmd",
    "CollectionExistsOp",
    "CollectionLoadOp",
    "CollectionMissingOp",
    "CollectionStoreCmd",
]


class CollectionLoadOp[T](Query[T | Sentinel]):
    """Read collection from parent. Returns EMPTY if missing."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> T | Sentinel:
        return await self.children[0].afirst(ctx)

    def run(self, ctx: Context) -> T | Sentinel:
        return self.children[0].first(ctx)

    def __repr__(self) -> str:
        return f"CollectionLoadOp({self.children[0]!r})"


class CollectionStoreCmd[T](Command):
    """Write collection to parent: parent[address] = data."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(self, ref: Ref, data: Nu[T | Sentinel]) -> None:
        super().__init__(ref, data)

    async def arun(self, ctx: Context) -> None:
        data = await self.children[1].afirst(ctx)
        if isinstance(data, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {data}")
        ref = self.children[0]
        parent = await ref.afetch_parent(ctx)
        address = await ref.aresolve_address(ctx)
        parent[address] = data

    def run(self, ctx: Context) -> None:
        data = self.children[1].first(ctx)
        if isinstance(data, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {data}")
        ref = self.children[0]
        parent = ref.fetch_parent(ctx)
        address = ref.resolve_address(ctx)
        parent[address] = data

    def __repr__(self) -> str:
        return f"CollectionStoreCmd({self.children[0]!r}, {self.children[1]!r})"


class CollectionEraseCmd(Command):
    """Delete collection from parent: del parent[address]."""

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> None:
        ref = self.children[0]
        parent = await ref.afetch_parent(ctx)
        address = await ref.aresolve_address(ctx)
        del parent[address]

    def run(self, ctx: Context) -> None:
        ref = self.children[0]
        parent = ref.fetch_parent(ctx)
        address = ref.resolve_address(ctx)
        del parent[address]

    def __repr__(self) -> str:
        return f"CollectionEraseCmd({self.children[0]!r})"


class CollectionExistsOp(Query[bool]):
    """Check if collection exists: not is_sentinel(ref value)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> bool:
        val = await self.children[0].afirst(ctx)
        return not is_sentinel(val)

    def run(self, ctx: Context) -> bool:
        val = self.children[0].first(ctx)
        return not is_sentinel(val)

    def __repr__(self) -> str:
        return f"CollectionExistsOp({self.children[0]!r})"


class CollectionMissingOp(Query[bool]):
    """Check if collection is missing: is_sentinel(ref value)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> bool:
        val = await self.children[0].afirst(ctx)
        return is_sentinel(val)

    def run(self, ctx: Context) -> bool:
        val = self.children[0].first(ctx)
        return is_sentinel(val)

    def __repr__(self) -> str:
        return f"CollectionMissingOp({self.children[0]!r})"
