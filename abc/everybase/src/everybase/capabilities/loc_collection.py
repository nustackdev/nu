# ruff: noqa: D102
"""Collection-level capability bases — extract, store, length, clear, exists.

CollectionExtractableBase: .get() wrapping ExtractOp
CollectionStorableBase: .store(data) wrapping StoreCmd
CollectionLengthableBase: .length() wrapping CollectionLenOp
CollectionClearableBase: .clear() wrapping CollectionClearCmd
CollectionExistableBase: .exists(), .missing()

These bases are for refs that represent collections/views.
The ref must implement fetch(ctx) -> storage object.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
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
        from everybase.morphisms.loc_collection import CollectionExistsOp

        return BoolValue(CollectionExistsOp(self))

    def missing(self) -> BoolValue:
        from everybase.morphisms.loc_collection import CollectionMissingOp

        return BoolValue(CollectionMissingOp(self))


class CollectionExtractableBase[CollectionTypeT](ABC):
    """Base for collection refs that can extract their contents as a Python value.

    Provides get() using ExtractOp. Subclasses must implement result()
    to wrap the operation in the correct typed container.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT: ...

    def get(self) -> CollectionTypeT:
        from everybase.morphisms.loc_collection import ExtractOp

        return self.result(ExtractOp(self))


class CollectionStorableBase[CollectionTypeT, CollectionT](ABC):
    """Base for collection refs that can replace their contents.

    Provides store(data) using StoreCmd. Subclasses must implement result()
    to wrap the operation in the correct typed container.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT: ...

    def store(
        self, value: CollectionT | Sentinel | Term[CollectionT | Sentinel]
    ) -> CollectionTypeT:
        from everybase.morphisms.loc_collection import StoreCmd
        from everybase.utils import ensure_term

        return self.result(StoreCmd(self, ensure_term(value)))


class CollectionLengthableBase:
    """Base for collection refs that can report their length.

    Provides length() using CollectionLenOp.
    """

    def length(self) -> IntValue:
        from everybase.morphisms.loc_collection import CollectionLenOp

        return IntValue(CollectionLenOp(self))


class CollectionClearableBase:
    """Base for collection refs that can be cleared.

    Provides clear() using CollectionClearCmd.
    """

    def clear(self) -> NoneValue:
        from everybase.morphisms.loc_collection import CollectionClearCmd

        return NoneValue(CollectionClearCmd(self))
