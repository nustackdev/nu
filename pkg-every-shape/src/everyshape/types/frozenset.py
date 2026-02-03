"""FrozenSet type — immutable set.

FrozenSetBase         = everybase.SetLikeBase + capabilities (frozenset IS immutable)
ReactiveFrozenSetBase = FrozenSetBase + ViewObservable

Goes directly to everybase since there is no everyshape set collection base yet.
"""

from __future__ import annotations

from everybase.abc import SetLikeBase as _EB_SetLikeBase
from everyshape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
    ViewObservableBase,
)


__all__ = [
    "FrozenSetBase",
    "ReactiveFrozenSetBase",
]


class FrozenSetBase[T](
    _EB_SetLikeBase[frozenset[T], T, object, object],
    CollectionExistableBase,
    CollectionExtractableBase[object],
):
    """FrozenSet — immutable set."""


class ReactiveFrozenSetBase[T](
    FrozenSetBase[T],
    ViewObservableBase,
):
    """Reactive frozenset — immutable + observable."""
