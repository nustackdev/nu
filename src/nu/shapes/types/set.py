"""Set type — mutable set.

SetI         = MutableSetBase (set IS mutable)
ReactiveSetType = SetI + ViewObservable
"""

from __future__ import annotations

from nu.interfaces import Interface
from ..collections.set import MutableSetBase as _MutableSetBase
from ..collections.set import ReactiveSetBase as _ReactiveSetBase


__all__ = [
    "ReactiveSetType",
    "SetType",
]


class SetType[T](
    _MutableSetBase[T, object, object],
    Interface[set],
):
    """Set — mutable set."""


class ReactiveSetType[T](
    SetType[T],
    _ReactiveSetBase[T, object, object],
    Interface[set],
):
    """Reactive set — mutable + observable."""
