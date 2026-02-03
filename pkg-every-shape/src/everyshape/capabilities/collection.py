# ruff: noqa: D102
"""Collection-level capability bases — extract, store, clear, exists.

CollectionExtractableBase: .get() wrapping ExtractOp
CollectionStorableBase: .store(data) wrapping StoreCmd
CollectionClearableBase: .clear() wrapping CollectionClearCmd
CollectionExistableBase: .exists(), .missing()

These bases are for refs that represent collections/views.
The ref must implement fetch(ctx) -> storage object.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everybase.values import BoolValue, IntValue, NoneValue


if TYPE_CHECKING:
    from everyabc import Sentinel, Term


__all__ = [
    "CollectionClearableBase",
    "CollectionExistableBase",
    "CollectionExtractableBase",
    "CollectionLengthableBase",
    "CollectionStorableBase",
]


class CollectionExistableBase:
    """Base for collection refs that can check existence.

    Provides exists() and missing() using CollectionExistsOp/CollectionMissingOp.
    """

    def exists(self) -> BoolValue:
        from everyshape.morphisms.collection import CollectionExistsOp

        return BoolValue(CollectionExistsOp(self))

    def missing(self) -> BoolValue:
        from everyshape.morphisms.collection import CollectionMissingOp

        return BoolValue(CollectionMissingOp(self))


class CollectionExtractableBase[CollectionTypeT]:
    """Base for collection refs that can extract their contents as a Python value.

    Provides get() using ExtractOp. Subclasses must implement result()
    to wrap the operation in the correct typed container.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT: ...

    def get(self) -> CollectionTypeT:
        from everyshape.morphisms.collection import ExtractOp

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
        from everybase.utils import ensure_term
        from everyshape.morphisms.collection import StoreCmd

        return self.result(StoreCmd(self, ensure_term(value)))


class CollectionLengthableBase:
    """Base for collection refs that can report their length.

    Provides length() using CollectionLenOp.
    """

    def length(self) -> IntValue:
        from everyshape.morphisms.collection import CollectionLenOp

        return IntValue(CollectionLenOp(self))


class CollectionClearableBase:
    """Base for collection refs that can be cleared.

    Provides clear() using CollectionClearCmd.
    """

    def clear(self) -> NoneValue:
        from everyshape.morphisms.collection import CollectionClearCmd

        return NoneValue(CollectionClearCmd(self))
