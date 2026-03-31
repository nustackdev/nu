# ruff: noqa: D102
"""Collection-level capability bases — store, erase, exists.

Refs ARE terms — executing a collection ref reads its value (via fetch).
No separate load() needed.

CollectionSettableBase: .store(data) wrapping CollectionStoreCmd
CollectionDeletableBase: .erase() wrapping CollectionEraseCmd
CollectionExistableBase: .exists(), .missing()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.abc import BoolValue, NoneValue


if TYPE_CHECKING:
    from nu import Sentinel, Term


__all__ = [
    "CollectionDeletableBase",
    "CollectionExistableBase",
    "CollectionSettableBase",
]


class CollectionExistableBase:
    """Base for collection refs that can check existence.

    Provides exists() and missing() using CollectionExistsOp/CollectionMissingOp.
    """

    def exists(self) -> BoolValue:
        from nu.shape.morphisms.collection import CollectionExistsOp

        return BoolValue(CollectionExistsOp(self))

    def missing(self) -> BoolValue:
        from nu.shape.morphisms.collection import CollectionMissingOp

        return BoolValue(CollectionMissingOp(self))


class CollectionSettableBase[CollectionT]:
    """Base for collection refs that can replace their contents.

    Provides store(data) using CollectionStoreCmd, returning NoneValue.
    """

    def store(self, value: CollectionT | Sentinel | Term[CollectionT | Sentinel]) -> NoneValue:
        from nu.abc import ensure_term
        from nu.shape.morphisms.collection import CollectionStoreCmd

        return NoneValue(CollectionStoreCmd(self, ensure_term(value)))


class CollectionDeletableBase:
    """Base for collection refs that can be deleted from parent.

    Provides erase() using CollectionEraseCmd: del parent[address].
    """

    def erase(self) -> NoneValue:
        from nu.shape.morphisms.collection import CollectionEraseCmd

        return NoneValue(CollectionEraseCmd(self))
