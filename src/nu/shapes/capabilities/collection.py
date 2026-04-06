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

from nu.primitives import BoolI, NoneI


if TYPE_CHECKING:
    from nu import Nu, Sentinel


__all__ = [
    "CollectionDeletableBase",
    "CollectionExistableBase",
    "CollectionSettableBase",
]


class CollectionExistableBase:
    """Base for collection refs that can check existence.

    Provides exists() and missing() using CollectionExistsOp/CollectionMissingOp.
    """

    def exists(self) -> BoolI:
        from ..ops.collection import CollectionExistsOp

        return BoolI(CollectionExistsOp(self))

    def missing(self) -> BoolI:
        from ..ops.collection import CollectionMissingOp

        return BoolI(CollectionMissingOp(self))


class CollectionSettableBase[CollectionT]:
    """Base for collection refs that can replace their contents.

    Provides store(data) using CollectionStoreCmd, returning NoneI.
    """

    def store(self, value: CollectionT | Sentinel | Nu[CollectionT | Sentinel]) -> NoneI:
        from nu.utils import ensure_nu

        from ..ops.collection import CollectionStoreCmd

        return NoneI(CollectionStoreCmd(self, ensure_nu(value)))


class CollectionDeletableBase:
    """Base for collection refs that can be deleted from parent.

    Provides erase() using CollectionEraseCmd: del parent[address].
    """

    def erase(self) -> NoneI:
        from ..ops.collection import CollectionEraseCmd

        return NoneI(CollectionEraseCmd(self))
