"""FrozenSet type — immutable set.

FrozenSetType = everybase.SetLikeBase + capabilities (frozenset IS immutable)

Goes directly to everybase since everyshape's SetLikeBase is set-specific.
"""

from __future__ import annotations

from nu.abc import Object
from nu.abc import SetLikeBase as _EB_SetLikeBase
from nu.shape.capabilities import (
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
