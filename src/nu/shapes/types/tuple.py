"""Tuple type — immutable sequence.

TupleI = everybase.SequenceBase + capabilities (tuple IS immutable)

Goes directly to everybase since everyshape's SequenceBase is list-specific.
"""

from __future__ import annotations

from nu.interfaces import Interface
from nu.interfaces import SequenceBase as _EB_SequenceBase
from ..capabilities import (
    CollectionExistableBase,
)


__all__ = [
    "TupleType",
]


class TupleType[T](
    _EB_SequenceBase[tuple[T, ...], T, object, object],
    CollectionExistableBase,
    Interface[tuple],
):
    """Tuple — immutable sequence."""
