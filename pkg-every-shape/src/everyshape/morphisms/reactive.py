# ruff: noqa: D102
"""Reactive morphisms — change observation at various granularities.

OnChangeOp: Subscribe to all changes on a view
OnPrimitiveChangeOp: Subscribe to changes on a primitive value (via parent)
OnChildChangeOp: Subscribe to changes on a specific child
OnChildrenChangeOp: Subscribe to changes on all immediate children
OnDescendantsChangeOp: Subscribe to descendants matching a pattern

These operate on refs that implement fetch(ctx) or fetch_parent(ctx).
The storage objects must implement the relevant observable protocol
(on_change, on_child_change, on_children_change, on_descendents_change).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everybase import Morphism, Operation, Term
from everyshape.protocols import (
    ChildObservableProtocol,
    ChildrenObservableProtocol,
    DescendantsObservableProtocol,
    ObservableProtocol,
)


if TYPE_CHECKING:
    from everybase import Context


__all__ = [
    "ChangeOp",
    "OnChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
    "OnPrimitiveChangeOp",
]


class ChangeOp(Operation, Morphism[object]):
    """Base class for all change subscription operations.

    All change operations return a subscription handle that can be used
    to bind callbacks and receive notifications.
    """

    @abstractmethod
    async def execute(self, ctx: Context) -> object: ...


class OnChangeOp(ChangeOp):
    """Subscribe to all changes on a view/collection.

    The storage object must implement on_change() -> Subscription.

    The ref must implement:
        fetch(ctx) -> storage object with on_change() method
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> object:
        view = await self.ref.fetch(ctx)
        if not isinstance(view, ObservableProtocol):
            raise TypeError(f"{type(view).__name__} does not implement ObservableProtocol")
        return view.on_change()

    def __repr__(self) -> str:
        return f"OnChangeOp({self.ref!r})"


class OnPrimitiveChangeOp(ChangeOp):
    """Subscribe to changes on a primitive value.

    Uses the parent collection's on_child_change(address) to watch
    a specific item.

    The ref must implement:
        fetch_parent(ctx) -> storage object with on_child_change() method
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> object:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        if not isinstance(parent, ChildObservableProtocol):
            raise TypeError(f"{type(parent).__name__} does not implement ChildObservableProtocol")
        return parent.on_child_change(address)

    def __repr__(self) -> str:
        return f"OnPrimitiveChangeOp({self.ref!r})"


class OnChildChangeOp[A](ChangeOp):
    """Subscribe to changes on a specific child of a view.

    The storage object must implement on_child_change(key) -> Subscription.

    The ref must implement:
        fetch(ctx) -> storage object with on_child_change() method
    """

    def __init__(self, ref: object, address: A | Term[A]) -> None:
        super().__init__(ref)
        self.ref = ref
        self.address = address

    async def execute(self, ctx: Context) -> object:
        if isinstance(self.address, Term):
            address = await self.address.execute(ctx)
        else:
            address = self.address

        view = await self.ref.fetch(ctx)
        if not isinstance(view, ChildObservableProtocol):
            raise TypeError(f"{type(view).__name__} does not implement ChildObservableProtocol")
        return view.on_child_change(address)

    def __repr__(self) -> str:
        return f"OnChildChangeOp({self.ref!r}, {self.address!r})"


class OnChildrenChangeOp(ChangeOp):
    """Subscribe to changes on all immediate children of a view.

    The storage object must implement on_children_change() -> Subscription.

    The ref must implement:
        fetch(ctx) -> storage object with on_children_change() method
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> object:
        view = await self.ref.fetch(ctx)
        if not isinstance(view, ChildrenObservableProtocol):
            raise TypeError(f"{type(view).__name__} does not implement ChildrenObservableProtocol")
        return view.on_children_change()

    def __repr__(self) -> str:
        return f"OnChildrenChangeOp({self.ref!r})"


class OnDescendantsChangeOp(ChangeOp):
    """Subscribe to changes on descendants matching a pattern.

    The storage object must implement on_descendents_change(*pattern).

    The ref must implement:
        fetch(ctx) -> storage object with on_descendents_change() method
    """

    def __init__(self, ref: object, *pattern: object) -> None:
        super().__init__(ref)
        self.ref = ref
        self.pattern = pattern

    async def execute(self, ctx: Context) -> object:
        if not self.pattern:
            raise ValueError("Pattern cannot be empty for on_descendants_change")

        view = await self.ref.fetch(ctx)
        if not isinstance(view, DescendantsObservableProtocol):
            raise TypeError(
                f"{type(view).__name__} does not implement DescendantsObservableProtocol"
            )
        return view.on_descendents_change(self.pattern[0], *self.pattern[1:])

    def __repr__(self) -> str:
        return f"OnDescendantsChangeOp({self.ref!r}, {self.pattern!r})"
