# ruff: noqa: D102
"""Reactive ops - change observation at various granularities.

OnChangeOp: Subscribe to all changes on a view
OnPrimitiveChangeOp: Subscribe to changes on a primitive value (via parent)
OnChildChangeOp: Subscribe to changes on a specific child
OnChildrenChangeOp: Subscribe to changes on all immediate children
OnDescendantsChangeOp: Subscribe to descendants matching a pattern

These operate on refs that implement fetch(ctx) or fetch_parent(ctx).
The storage objects must implement the relevant on_* methods.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from nu.terms import Nu, Op


if TYPE_CHECKING:
    from nu import Context

    from nu.shapes.refs import Ref


__all__ = [
    "ChangeOp",
    "OnChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
    "OnPrimitiveChangeOp",
]


class ChangeOp(Op[object]):
    """Base class for all change subscription operations.

    All change operations return a subscription handle that can be used
    to bind callbacks and receive notifications.
    """

    @abstractmethod
    async def execute(self, ctx: Context) -> object: ...


class OnChangeOp(ChangeOp):
    """Subscribe to all changes on a view/collection.

    The ref must implement fetch(ctx) returning an object with on_change().
    """

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> object:
        view = await self.ref.fetch(ctx)
        return view.on_change()  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChangeOp({self.ref!r})"


class OnPrimitiveChangeOp(ChangeOp):
    """Subscribe to changes on a primitive value.

    Uses the parent collection's on_child_change(address) to watch
    a specific item.

    The ref must implement fetch_parent(ctx) and resolve_address(ctx).
    """

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> object:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return parent.on_child_change(address)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnPrimitiveChangeOp({self.ref!r})"


class OnChildChangeOp[A](ChangeOp):
    """Subscribe to changes on a specific child of a view.

    The ref must implement fetch(ctx) returning an object with on_child_change().
    """

    def __init__(self, ref: Ref, address: A | Nu[A]) -> None:
        super().__init__(ref)
        self.ref = ref
        self.address = address

    async def execute(self, ctx: Context) -> object:
        if isinstance(self.address, Nu):
            address = await self.address.execute(ctx)
        else:
            address = self.address

        view = await self.ref.fetch(ctx)
        return view.on_child_change(address)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChildChangeOp({self.ref!r}, {self.address!r})"


class OnChildrenChangeOp(ChangeOp):
    """Subscribe to changes on all immediate children of a view.

    The ref must implement fetch(ctx) returning an object with on_children_change().
    """

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> object:
        view = await self.ref.fetch(ctx)
        return view.on_children_change()  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChildrenChangeOp({self.ref!r})"


class OnDescendantsChangeOp(ChangeOp):
    """Subscribe to changes on descendants matching a pattern.

    The ref must implement fetch(ctx) returning an object with on_descendents_change().
    """

    def __init__(self, ref: Ref, *pattern: object) -> None:
        super().__init__(ref)
        self.ref = ref
        self.pattern = pattern

    async def execute(self, ctx: Context) -> object:
        if not self.pattern:
            raise ValueError("Pattern cannot be empty for on_descendants_change")

        view = await self.ref.fetch(ctx)
        return view.on_descendents_change(self.pattern[0], *self.pattern[1:])  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnDescendantsChangeOp({self.ref!r}, {self.pattern!r})"
