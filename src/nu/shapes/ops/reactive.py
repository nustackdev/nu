# ruff: noqa: D102
"""Reactive ops - change observation at various granularities.

OnChangeOp: Subscribe to all changes on a view
OnPrimitiveChangeOp: Subscribe to changes on a primitive value (via parent)
OnChildChangeOp: Subscribe to changes on a specific child
OnChildrenChangeOp: Subscribe to changes on all immediate children
OnDescendantsChangeOp: Subscribe to descendants matching a pattern

All ops use children[0].execute() to get the view (goes through Snapshot wrapper).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from nu.terms import Nu, Op
from nu.terms.effect import Direction


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
    """Base class for all change subscription operations."""

    @abstractmethod
    async def execute(self, ctx: Context) -> object: ...


class OnChangeOp(ChangeOp):
    """Subscribe to all changes on a view/collection."""

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> object:
        view = await self.children[0].execute(ctx)
        return view.on_change()  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChangeOp({self.children[0]!r})"


class OnPrimitiveChangeOp(ChangeOp):
    """Subscribe to changes on a primitive value.

    Uses the parent ref's view to subscribe on_child_change.
    Navigates through children[0] (the PrimitiveRef) to get parent + address.
    Has READ override so auto_atomic doesn't Snapshot-wrap the Ref child
    (the Op needs raw Ref access for fetch_parent/resolve_address).
    """

    overrides = {0: Direction.READ}

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> object:
        ref = self.children[0]
        parent = await ref.fetch_parent(ctx)
        address = await ref.resolve_address(ctx)
        return parent.on_child_change(address)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnPrimitiveChangeOp({self.children[0]!r})"


class OnChildChangeOp[A](ChangeOp):
    """Subscribe to changes on a specific child of a view."""

    def __init__(self, ref: Ref, address: A | Nu[A]) -> None:
        super().__init__(ref)
        self.address = address

    async def execute(self, ctx: Context) -> object:
        if isinstance(self.address, Nu):
            address = await self.address.execute(ctx)
        else:
            address = self.address

        view = await self.children[0].execute(ctx)
        return view.on_child_change(address)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChildChangeOp({self.children[0]!r}, {self.address!r})"


class OnChildrenChangeOp(ChangeOp):
    """Subscribe to changes on all immediate children of a view."""

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> object:
        view = await self.children[0].execute(ctx)
        return view.on_children_change()  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChildrenChangeOp({self.children[0]!r})"


class OnDescendantsChangeOp(ChangeOp):
    """Subscribe to descendants matching a pattern."""

    def __init__(self, ref: Ref, *pattern: object) -> None:
        super().__init__(ref)
        self.pattern = pattern

    async def execute(self, ctx: Context) -> object:
        if not self.pattern:
            raise ValueError("Pattern cannot be empty for on_descendants_change")

        view = await self.children[0].execute(ctx)
        return view.on_descendents_change(self.pattern[0], *self.pattern[1:])  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnDescendantsChangeOp({self.children[0]!r}, {self.pattern!r})"
