# ruff: noqa: D102
"""Collection-level capability bases — get, set, delete, exists.

Same API as item capabilities but distinct morphism nodes for deformation
matching. All use parent[address] primitives.

CollectionGettableBase: .get() wrapping CollectionGetOp
CollectionSettableBase: .set(data) wrapping CollectionSetCmd
CollectionDeletableBase: .remove() wrapping CollectionDeleteCmd
CollectionExistableBase: .exists(), .missing()
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everybase.abc import BoolValue, NoneValue


if TYPE_CHECKING:
    from everybase import Sentinel, Term


__all__ = [
    "CollectionDeletableBase",
    "CollectionExistableBase",
    "CollectionGettableBase",
    "CollectionSettableBase",
]


class CollectionExistableBase:
    """Base for collection refs that can check existence.

    Provides exists() and missing() using CollectionExistsOp/CollectionMissingOp.
    """

    def exists(self) -> BoolValue:
        from everybase.shape.morphisms.collection import CollectionExistsOp

        return BoolValue(CollectionExistsOp(self))

    def missing(self) -> BoolValue:
        from everybase.shape.morphisms.collection import CollectionMissingOp

        return BoolValue(CollectionMissingOp(self))


class CollectionGettableBase[CollectionTypeT]:
    """Base for collection refs that can read their value.

    Provides get() using CollectionGetOp.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT: ...

    def get(self) -> CollectionTypeT:
        from everybase.shape.morphisms.collection import CollectionGetOp

        return self.result(CollectionGetOp(self))


class CollectionSettableBase[CollectionTypeT, CollectionT]:
    """Base for collection refs that can replace their contents.

    Provides set(data) using CollectionSetCmd.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT: ...

    def set(self, value: CollectionT | Sentinel | Term[CollectionT | Sentinel]) -> CollectionTypeT:
        from everybase.abc import ensure_term
        from everybase.shape.morphisms.collection import CollectionSetCmd

        return self.result(CollectionSetCmd(self, ensure_term(value)))


class CollectionDeletableBase:
    """Base for collection refs that can be deleted from parent.

    Provides remove() using CollectionDeleteCmd: del parent[address].
    """

    def remove(self) -> NoneValue:
        from everybase.shape.morphisms.collection import CollectionDeleteCmd

        return NoneValue(CollectionDeleteCmd(self))
