"""Tuple type — immutable sequence.

TupleType = everybase.SequenceBase + capabilities (tuple IS immutable)

Goes directly to everybase since eb_shape's SequenceBase is list-specific.
"""

from __future__ import annotations

from eb_shape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
)
from everybase.abc import SequenceBase as _EB_SequenceBase
from everybase.abc import TypeBase


__all__ = [
    "TupleType",
]


class TupleType[T](
    _EB_SequenceBase[tuple[T, ...], T, object, object],
    CollectionExistableBase,
    CollectionExtractableBase[object],
    TypeBase[tuple],
):
    """Tuple — immutable sequence."""
