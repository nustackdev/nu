# ruff: noqa: D102
"""Collection base hierarchy - lifecycle ops for collections in the document model.

Three tiers:
    CollectionForm          exists(), missing()
    MutableCollectionI   + store(), erase()
    ReactiveCollectionI  + on_change(), on_child_change(), ...

Mirrors nu.forms.collections.abc pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.primitives import BoolForm
from nu.terms import Form


if TYPE_CHECKING:
    from nu import Nu, Sentinel
    from nu.shapes.ops import OnChangeOp, OnChildChangeOp, OnChildrenChangeOp, OnDescendantsChangeOp


__all__ = [
    "CollectionForm",
    "MutableCollectionI",
    "ReactiveCollectionI",
]


class CollectionForm(Form):
    """Collection in a document - can check existence."""

    def exists(self) -> BoolForm:
        from nu.shapes.ops import CollectionExistsOp

        return BoolForm(CollectionExistsOp(self))

    def missing(self) -> BoolForm:
        from nu.shapes.ops import CollectionMissingOp

        return BoolForm(CollectionMissingOp(self))

    def extract(self) -> Nu:
        from nu.shapes.ops import CollectionExtractOp

        return CollectionExtractOp(self)


class MutableCollectionI[CollectionT](CollectionForm):
    """Mutable collection - can store and erase."""

    def store(self, value: CollectionT | Sentinel | Nu[CollectionT | Sentinel]) -> Nu:
        from nu.shapes.ops import CollectionStoreCmd

        return CollectionStoreCmd(self, value)

    def erase(self) -> Nu:
        from nu.shapes.ops import CollectionEraseCmd

        return CollectionEraseCmd(self)


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
