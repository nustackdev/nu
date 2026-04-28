"""Reactive ops - change observation at various granularities.

OnChangeOp: Subscribe to all changes on a view
OnChildChangeOp: Subscribe to changes on a specific child
OnChildrenChangeOp: Subscribe to changes on all immediate children
OnDescendantsChangeOp: Subscribe to descendants matching a pattern

All ops read the view via children[0] (goes through Snapshot wrapper).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.protocol import Nu
from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.shapes.refs import Ref


__all__ = [
    "ChangeOp",
    "OnChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ChangeOp(ScalarQuery):
    """Base class for all change subscription operations."""

    accepts_sentinels: ClassVar[bool] = True


class OnChangeOp(ChangeOp):
    """Subscribe to all changes on a view/collection."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> object:  # noqa: ANN401
        view = ops[0]
        return view.on_change()

    def __repr__(self) -> str:
        return f"OnChangeOp({self._children[0]!r})"


class OnChildChangeOp(ChangeOp):
    """Subscribe to changes on a specific child of a view."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: Ref, address: object) -> None:
        super().__init__(ref)
        self.address = address

    def _apply(self, ctx: Any, ops: list[Any]) -> object:  # noqa: ANN401
        from nu import runtime

        if isinstance(self.address, Nu):
            address = runtime.first(self.address, ctx)
        else:
            address = self.address

        view = ops[0]
        return view.on_child_change(address)

    async def _aapply(self, ctx: Any, ops: list[Any]) -> object:  # noqa: ANN401
        from nu import runtime

        if isinstance(self.address, Nu):
            address = await runtime.afirst(self.address, ctx)
        else:
            address = self.address

        view = ops[0]
        return view.on_child_change(address)

    def __repr__(self) -> str:
        return f"OnChildChangeOp({self._children[0]!r}, {self.address!r})"


class OnChildrenChangeOp(ChangeOp):
    """Subscribe to changes on all immediate children of a view."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> object:  # noqa: ANN401
        view = ops[0]
        return view.on_children_change()

    def __repr__(self) -> str:
        return f"OnChildrenChangeOp({self._children[0]!r})"


class OnDescendantsChangeOp(ChangeOp):
    """Subscribe to descendants matching a pattern."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: Ref, *pattern: object) -> None:
        super().__init__(ref)
        self.pattern = pattern

    def _apply(self, ctx: Any, ops: list[Any]) -> object:  # noqa: ANN401
        if not self.pattern:
            raise ValueError("Pattern cannot be empty for on_descendants_change")

        view = ops[0]
        return view.on_descendents_change(self.pattern[0], *self.pattern[1:])

    def __repr__(self) -> str:
        return f"OnDescendantsChangeOp({self._children[0]!r}, {self.pattern!r})"
