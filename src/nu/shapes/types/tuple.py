"""Tuple type — immutable sequence.

TupleI = everybase.SequenceBase + capabilities (tuple IS immutable)

Goes directly to everybase since everyshape's SequenceBase is list-specific.
"""

from __future__ import annotations

from nu.collections.abc import SequenceBase as _EB_SequenceBase
from nu.interface import Interface

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
