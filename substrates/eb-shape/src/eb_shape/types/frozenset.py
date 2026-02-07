"""FrozenSet type — immutable set.

FrozenSetType = everybase.SetLikeBase + capabilities (frozenset IS immutable)

Goes directly to everybase since eb_shape's SetLikeBase is set-specific.
"""

from __future__ import annotations

from eb_shape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
)
from everybase.abc import SetLikeBase as _EB_SetLikeBase
from everybase.abc import TypeBase


__all__ = [
    "FrozenSetType",
]


class FrozenSetType[T](
    _EB_SetLikeBase[frozenset[T], T, object, object],
    CollectionExistableBase,
    CollectionExtractableBase[object],
    TypeBase[frozenset],
):
    """FrozenSet — immutable set."""
