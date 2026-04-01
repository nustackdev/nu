"""FrozenSet type — immutable set.

FrozenSetType = everybase.SetLikeBase + capabilities (frozenset IS immutable)

Goes directly to everybase since everyshape's SetLikeBase is set-specific.
"""

from __future__ import annotations

from nu.interfaces.types import Object
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
    Object[frozenset],
):
    """FrozenSet — immutable set."""
