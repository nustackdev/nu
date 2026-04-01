# ruff: noqa: D102
"""Reactive capability bases — change observation at various granularities.

PrimitiveObservableBase: .on_change() for primitive/item refs
ViewObservableBase: .on_change(), .on_child_change(), .on_children_change(),
                    .on_descendants_change() for collection/view refs

These bases are for refs that support change observation.
Primitive refs use fetch_parent(ctx) + resolve_address(ctx).
View refs use fetch(ctx).
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu import Sentinel, Term
    from nu.shapes.ops.reactive import (
        OnChangeOp,
        OnChildChangeOp,
        OnChildrenChangeOp,
        OnDescendantsChangeOp,
        OnPrimitiveChangeOp,
    )


__all__ = [
    "PrimitiveObservableBase",
    "ViewObservableBase",
]


class PrimitiveObservableBase:
    """Base for primitive/item refs that support change observation.

    Provides on_change() using OnPrimitiveChangeOp which subscribes
    via the parent collection's on_child_change(address).
    """

    def on_change(self) -> OnPrimitiveChangeOp:
        from nu.shapes.ops.reactive import OnPrimitiveChangeOp

        return OnPrimitiveChangeOp(self)


class ViewObservableBase:
    """Base for collection/view refs that support change observation.

    Provides observation at multiple granularities:
    - on_change(): watch all changes in this view
    - on_child_change(address): watch a specific child
    - on_children_change(): watch all immediate children
    - on_descendants_change(*pattern): watch descendants matching pattern
    """

    def on_change(self) -> OnChangeOp:
        from nu.shapes.ops.reactive import OnChangeOp

        return OnChangeOp(self)

    def on_child_change(self, address: str | Sentinel | Term[str | Sentinel]) -> OnChildChangeOp:
        from nu.shapes.ops.reactive import OnChildChangeOp

        return OnChildChangeOp(self, address)

    def on_children_change(self) -> OnChildrenChangeOp:
        from nu.shapes.ops.reactive import OnChildrenChangeOp

        return OnChildrenChangeOp(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChangeOp:
        from nu.shapes.ops.reactive import OnDescendantsChangeOp

        return OnDescendantsChangeOp(self, *pattern)
