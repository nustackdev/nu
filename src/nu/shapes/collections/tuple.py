"""Shaped TupleI - immutable sequence in the document model.

Goes directly to nu.collections.abc since shapes' SequenceI is list-specific.
"""

from __future__ import annotations

from nu.collections.abc import SequenceBase as _SequenceBase
from nu.interface import Interface

from .abc import CollectionI


__all__ = [
    "TupleI",
]


class TupleI[T](
    _SequenceBase[tuple[T, ...], T, object, object],
    CollectionI,
    Interface[tuple],
):
    """Shaped tuple - immutable sequence with collection ops."""
