"""Set type — mutable set.

SetType         = MutableSetBase (set IS mutable)
ReactiveSetType = SetType + ViewObservable
"""

from __future__ import annotations

from eb_shape.collections.set import MutableSetBase as _MutableSetBase
from eb_shape.collections.set import ReactiveSetBase as _ReactiveSetBase
from everybase.abc import TypeBase


__all__ = [
    "ReactiveSetType",
    "SetType",
]


class SetType[T](
    _MutableSetBase[T, object, object],
    TypeBase[set],
):
    """Set — mutable set."""


class ReactiveSetType[T](
    SetType[T],
    _ReactiveSetBase[T, object, object],
    TypeBase[set],
):
    """Reactive set — mutable + observable."""
