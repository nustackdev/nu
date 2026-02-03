"""Tuple type — immutable sequence.

TupleBase         = everybase.SequenceBase + capabilities (tuple IS immutable)
ReactiveTupleBase = TupleBase + ViewObservable

Goes directly to everybase since everyshape's SequenceBase is list-specific.
"""

from __future__ import annotations

from everybase.collections import SequenceBase as _EB_SequenceBase
from everyshape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
    ViewObservableBase,
)


__all__ = [
    "ReactiveTupleBase",
    "TupleBase",
]


class TupleBase[T](
    _EB_SequenceBase[tuple[T, ...], T, object, object],
    CollectionExistableBase,
    CollectionExtractableBase[object],
):
    """Tuple — immutable sequence."""


class ReactiveTupleBase[T](
    TupleBase[T],
    ViewObservableBase,
):
    """Reactive tuple — immutable + observable."""
