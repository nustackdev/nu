"""Tuple type - immutable sequence.

TupleType = nu.collections.abc.SequenceBase + CollectionBase (tuple IS immutable).

Goes directly to nu.collections.abc since shapes' SequenceBase is list-specific.
"""

from __future__ import annotations

from nu.collections.abc import SequenceBase as _SequenceBase
from nu.interface import Interface

from .abc import CollectionBase


__all__ = [
    "TupleType",
]


class TupleType[T](
    _SequenceBase[tuple[T, ...], T, object, object],
    CollectionBase,
    Interface[tuple],
):
    """Tuple - immutable sequence."""
