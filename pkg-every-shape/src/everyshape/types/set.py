"""Set type — mutable set.

SetBase         = everybase.MutableSetBase + capabilities (set IS mutable)
ReactiveSetBase = SetBase + ViewObservable

Goes directly to everybase since there is no everyshape set collection base yet.
"""

from __future__ import annotations

from everybase.abc import MutableSetBase as _EB_MutableSetBase
from everyshape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionStorableBase,
    ViewObservableBase,
)


__all__ = [
    "ReactiveSetBase",
    "SetBase",
]


class SetBase[T](
    _EB_MutableSetBase[set[T], T, object, object],
    CollectionExistableBase,
    CollectionExtractableBase[object],
    CollectionStorableBase[object, set[T]],
):
    """Set — mutable set."""


class ReactiveSetBase[T](
    SetBase[T],
    ViewObservableBase,
):
    """Reactive set — mutable + observable."""
