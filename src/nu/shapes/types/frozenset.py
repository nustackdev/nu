"""FrozenSet type — immutable set.

FrozenSetI = everybase.SetLikeBase + capabilities (frozenset IS immutable)

Goes directly to everybase since everyshape's SetLikeBase is set-specific.
"""

from __future__ import annotations

from nu.interfaces import Interface
from nu.interfaces.collections_abc import SetLikeBase as _EB_SetLikeBase
from nu.shapes.capabilities import (
    CollectionExistableBase,
)


__all__ = [
    "FrozenSetType",
]


class FrozenSetType[T](
    _EB_SetLikeBase[frozenset[T], T, object, object],
    CollectionExistableBase,
    Interface[frozenset],
):
    """FrozenSet — immutable set."""
