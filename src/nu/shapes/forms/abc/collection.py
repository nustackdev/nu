# ruff: noqa: D102
"""Collection base hierarchy - lifecycle ops for collections in the document model.

Three tiers:
    CollectionForm          exists(), missing()
    MutableCollectionForm   + store(), erase()
    ReactiveCollectionForm  + on_change(), on_child_change(), ...

Mirrors nu.forms.collections.abc pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.primitives import BoolForm
from nu.terms import Form


if TYPE_CHECKING:
    from nu import Nu, Sentinel
    from nu.shapes.queries import OnChange, OnChildChange, OnChildrenChange, OnDescendantsChange


__all__ = [
    "CollectionForm",
    "MutableCollectionForm",
    "ReactiveCollectionForm",
]


class CollectionForm(Form):
    """Collection in a document - can check existence."""

    def exists(self) -> BoolForm:
        from nu.shapes.queries import CollectionExists

        return BoolForm(CollectionExists(self))

    def missing(self) -> BoolForm:
        from nu.shapes.queries import CollectionMissing

        return BoolForm(CollectionMissing(self))

    def extract(self) -> Nu:
        from nu.shapes.queries import CollectionExtract

        return CollectionExtract(self)


class MutableCollectionForm[CollectionT](CollectionForm):
    """Mutable collection - can store and erase."""

    def store(self, value: CollectionT | Sentinel | Nu[CollectionT | Sentinel]) -> Nu:
        from nu.shapes.commands import CollectionStoreCmd

        return CollectionStoreCmd(self, value)

    def erase(self) -> Nu:
        from nu.shapes.commands import CollectionEraseCmd

        return CollectionEraseCmd(self)


class ReactiveCollectionForm[CollectionT](MutableCollectionForm[CollectionT]):
    """Reactive collection - can observe changes."""

    def on_change(self) -> OnChange:
        from nu.shapes.queries import OnChange

        return OnChange(self)

    def on_child_change(self, address: str | Sentinel | Nu[str | Sentinel]) -> OnChildChange:
        from nu.shapes.queries import OnChildChange

        return OnChildChange(self, address)

    def on_children_change(self) -> OnChildrenChange:
        from nu.shapes.queries import OnChildrenChange

        return OnChildrenChange(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChange:
        from nu.shapes.queries import OnDescendantsChange

        return OnDescendantsChange(self, *pattern)
