"""FrozenSet type — immutable set.

FrozenSetType = everybase.SetLikeBase + capabilities (frozenset IS immutable)

Goes directly to everybase since everyshape's SetLikeBase is set-specific.
"""

from __future__ import annotations

from everybase.abc import Object
from everybase.abc import SetLikeBase as _EB_SetLikeBase
from everybase.shape.capabilities import (
    CollectionExistableBase,
    CollectionGettableBase,
)


__all__ = [
    "FrozenSetType",
]


class FrozenSetType[T](
    _EB_SetLikeBase[frozenset[T], T, object, object],
    CollectionExistableBase,
    CollectionGettableBase[object],
    Object[frozenset],
):
    """FrozenSet — immutable set."""
