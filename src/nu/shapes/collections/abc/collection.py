# ruff: noqa: D102
"""Collection base hierarchy - lifecycle ops for collections in the document model.

Three tiers:
    CollectionI          exists(), missing()
    MutableCollectionI   + store(), erase()
    ReactiveCollectionI  + on_change(), on_child_change(), ...

Mirrors nu.collections.abc pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.primitives import BoolI, NoneI
from nu.terms import Interface


if TYPE_CHECKING:
    from nu import Nu, Sentinel
    from nu.shapes.ops import OnChangeOp, OnChildChangeOp, OnChildrenChangeOp, OnDescendantsChangeOp


__all__ = [
    "CollectionI",
    "MutableCollectionI",
    "ReactiveCollectionI",
]


class CollectionI(Interface):
    """Collection in a document - can check existence."""

    def exists(self) -> BoolI:
        from nu.shapes.ops import CollectionExistsOp

        return BoolI(CollectionExistsOp(self))

    def missing(self) -> BoolI:
        from nu.shapes.ops import CollectionMissingOp

        return BoolI(CollectionMissingOp(self))


class MutableCollectionI[CollectionT](CollectionI):
    """Mutable collection - can store and erase."""

    def store(self, value: CollectionT | Sentinel | Nu[CollectionT | Sentinel]) -> NoneI:
        from nu.shapes.ops import CollectionStoreCmd
        from nu.utils import ensure_nu

        return NoneI(CollectionStoreCmd(self, ensure_nu(value)))

    def erase(self) -> NoneI:
        from nu.shapes.ops import CollectionEraseCmd

        return NoneI(CollectionEraseCmd(self))


class ReactiveCollectionI[CollectionT](MutableCollectionI[CollectionT]):
    """Reactive collection - can observe changes."""

    def on_change(self) -> OnChangeOp:
        from nu.shapes.ops import OnChangeOp

        return OnChangeOp(self)

    def on_child_change(self, address: str | Sentinel | Nu[str | Sentinel]) -> OnChildChangeOp:
        from nu.shapes.ops import OnChildChangeOp

        return OnChildChangeOp(self, address)

    def on_children_change(self) -> OnChildrenChangeOp:
        from nu.shapes.ops import OnChildrenChangeOp

        return OnChildrenChangeOp(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChangeOp:
        from nu.shapes.ops import OnDescendantsChangeOp

        return OnDescendantsChangeOp(self, *pattern)
