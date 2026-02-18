"""Tuple type — immutable sequence.

TupleType = everybase.SequenceBase + capabilities (tuple IS immutable)

Goes directly to everybase since everyshape's SequenceBase is list-specific.
"""

from __future__ import annotations

from everybase.abc import SequenceBase as _EB_SequenceBase
from everybase.abc import TypeBase
from everyshape.capabilities import (
    CollectionExistableBase,
    CollectionExtractableBase,
)


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
