# ruff: noqa: D102
"""Reactive ops - change observation at various granularities.

OnChangeOp: Subscribe to all changes on a view
OnChildChangeOp: Subscribe to changes on a specific child
OnChildrenChangeOp: Subscribe to changes on all immediate children
OnDescendantsChangeOp: Subscribe to descendants matching a pattern

All ops read the view via children[0] (goes through Snapshot wrapper).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Mode, Nu, Query


if TYPE_CHECKING:
    from nu import Context
    from nu.shapes.refs import Ref


__all__ = [
    "ChangeOp",
    "OnChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
]


class ChangeOp(Query[object]):
    """Base class for all change subscription operations."""

    @abstractmethod
    async def arun(self, ctx: Context) -> object: ...


class OnChangeOp(ChangeOp):
    """Subscribe to all changes on a view/collection."""

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> object:
        view = await self.children[0].afirst(ctx)
        return view.on_change()  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChangeOp({self.children[0]!r})"


class OnChildChangeOp[A](ChangeOp):
    """Subscribe to changes on a specific child of a view."""

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, ref: Ref, address: A | Nu[A]) -> None:
        super().__init__(ref)
        self.address = address

    async def arun(self, ctx: Context) -> object:
        if isinstance(self.address, Nu):
            address = await self.address.afirst(ctx)
        else:
            address = self.address

        view = await self.children[0].afirst(ctx)
        return view.on_child_change(address)  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChildChangeOp({self.children[0]!r}, {self.address!r})"


class OnChildrenChangeOp(ChangeOp):
    """Subscribe to changes on all immediate children of a view."""

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> object:
        view = await self.children[0].afirst(ctx)
        return view.on_children_change()  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnChildrenChangeOp({self.children[0]!r})"


class OnDescendantsChangeOp(ChangeOp):
    """Subscribe to descendants matching a pattern."""

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, ref: Ref, *pattern: object) -> None:
        super().__init__(ref)
        self.pattern = pattern

    async def arun(self, ctx: Context) -> object:
        if not self.pattern:
            raise ValueError("Pattern cannot be empty for on_descendants_change")

        view = await self.children[0].afirst(ctx)
        return view.on_descendents_change(self.pattern[0], *self.pattern[1:])  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"OnDescendantsChangeOp({self.children[0]!r}, {self.pattern!r})"
