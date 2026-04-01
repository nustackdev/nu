"""Tuple type — immutable sequence.

TupleType = everybase.SequenceBase + capabilities (tuple IS immutable)

Goes directly to everybase since everyshape's SequenceBase is list-specific.
"""

from __future__ import annotations

from nu.interfaces.types import Object
from nu.interfaces.collections_abc import SequenceBase as _EB_SequenceBase
from nu.shapes.capabilities import (
    CollectionExistableBase,
)


__all__ = [
    "TupleType",
]


class TupleType[T](
    _EB_SequenceBase[tuple[T, ...], T, object, object],
    CollectionExistableBase,
    Object[tuple],
):
    """Tuple — immutable sequence."""
