# ruff: noqa: D102
"""Collection-level capability bases — extract, store, clear, exists.

CollectionExtractableBase: .extract() wrapping ExtractOp
CollectionStorableBase: .store(data) wrapping StoreCmd
CollectionClearableBase: .clear() wrapping CollectionClearCmd
CollectionExistableBase: .exists(), .missing()

These bases are for refs that represent collections/views.
The ref must implement fetch(ctx) -> storage object.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everybase.abc import BoolValue, NoneValue


if TYPE_CHECKING:
    from everybase import Sentinel, Term


__all__ = [
    "CollectionClearableBase",
    "CollectionExistableBase",
    "CollectionExtractableBase",
    "CollectionStorableBase",
]


class CollectionExistableBase:
    """Base for collection refs that can check existence.

    Provides exists() and missing() using CollectionExistsOp/CollectionMissingOp.
    """

    def exists(self) -> BoolValue:
        from eb_shape.morphisms.collection import CollectionExistsOp

        return BoolValue(CollectionExistsOp(self))

    def missing(self) -> BoolValue:
        from eb_shape.morphisms.collection import CollectionMissingOp

        return BoolValue(CollectionMissingOp(self))


class CollectionExtractableBase[CollectionTypeT]:
    """Base for collection refs that can extract their contents as a Python value.

    Provides extract() using ExtractOp. Subclasses must implement result()
    to wrap the operation in the correct typed container.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT: ...

    def get(self) -> CollectionTypeT:
        from eb_shape.morphisms.collection import ExtractOp

        return self.result(ExtractOp(self))


class CollectionStorableBase[CollectionTypeT, CollectionT]:
    """Base for collection refs that can replace their contents.

    Provides store(data) using StoreCmd. Subclasses must implement result()
    to wrap the operation in the correct typed container.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT: ...

    def store(
        self, value: CollectionT | Sentinel | Term[CollectionT | Sentinel]
    ) -> CollectionTypeT:
        from eb_shape.morphisms.collection import StoreCmd
        from everybase.abc import ensure_term

        return self.result(StoreCmd(self, ensure_term(value)))


class CollectionClearableBase:
    """Base for collection refs that can be cleared.

    Provides clear() using CollectionClearCmd.
    """

    def clear(self) -> NoneValue:
        from eb_shape.morphisms.collection import CollectionClearCmd

        return NoneValue(CollectionClearCmd(self))
