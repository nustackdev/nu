# ruff: noqa: D102
"""Collection base hierarchy - lifecycle ops for collections in the document model.

Three tiers:
    CollectionBase          exists(), missing()
    MutableCollectionBase   + store(), erase()
    ReactiveCollectionBase  + on_change(), on_child_change(), on_children_change(),
                              on_descendants_change()

Mirrors nu.collections.abc pattern (CollectionBase -> MutableMapping -> ...).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.primitives import BoolI, NoneI


if TYPE_CHECKING:
    from nu import Nu, Sentinel

    from ...ops.reactive import (
        OnChangeOp,
        OnChildChangeOp,
        OnChildrenChangeOp,
        OnDescendantsChangeOp,
    )


__all__ = [
    "CollectionBase",
    "MutableCollectionBase",
    "ReactiveCollectionBase",
]


class CollectionBase:
    """Collection in a document - can check existence."""

    def exists(self) -> BoolI:
        from nu.shapes.ops.collection import CollectionExistsOp

        return BoolI(CollectionExistsOp(self))

    def missing(self) -> BoolI:
        from nu.shapes.ops.collection import CollectionMissingOp

        return BoolI(CollectionMissingOp(self))


class MutableCollectionBase[CollectionT](CollectionBase):
    """Mutable collection - can store and erase."""

    def store(self, value: CollectionT | Sentinel | Nu[CollectionT | Sentinel]) -> NoneI:
        from nu.utils import ensure_nu

        from nu.shapes.ops.collection import CollectionStoreCmd

        return NoneI(CollectionStoreCmd(self, ensure_nu(value)))

    def erase(self) -> NoneI:
        from nu.shapes.ops.collection import CollectionEraseCmd

        return NoneI(CollectionEraseCmd(self))


class ReactiveCollectionBase[CollectionT](MutableCollectionBase[CollectionT]):
    """Reactive collection - can observe changes."""

    def on_change(self) -> OnChangeOp:
        from nu.shapes.ops.reactive import OnChangeOp

        return OnChangeOp(self)

    def on_child_change(
        self, address: str | Sentinel | Nu[str | Sentinel]
    ) -> OnChildChangeOp:
        from nu.shapes.ops.reactive import OnChildChangeOp

        return OnChildChangeOp(self, address)

    def on_children_change(self) -> OnChildrenChangeOp:
        from nu.shapes.ops.reactive import OnChildrenChangeOp

        return OnChildrenChangeOp(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChangeOp:
        from nu.shapes.ops.reactive import OnDescendantsChangeOp

        return OnDescendantsChangeOp(self, *pattern)
