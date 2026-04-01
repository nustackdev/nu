"""Set type — mutable set.

SetType         = MutableSetBase (set IS mutable)
ReactiveSetType = SetType + ViewObservable
"""

from __future__ import annotations

from nu.interfaces.types import Object
from nu.shapes.collections.set import MutableSetBase as _MutableSetBase
from nu.shapes.collections.set import ReactiveSetBase as _ReactiveSetBase


__all__ = [
    "ReactiveSetType",
    "SetType",
]


class SetType[T](
    _MutableSetBase[T, object, object],
    Object[set],
):
    """Set — mutable set."""


class ReactiveSetType[T](
    SetType[T],
    _ReactiveSetBase[T, object, object],
    Object[set],
):
    """Reactive set — mutable + observable."""
