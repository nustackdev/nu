"""Collection capability protocol — Containable + Lengthable + Iterable.

Follows Python's collections.abc.Collection pattern.
"""

from __future__ import annotations

from typing import Protocol

from .col_atoms_protocol import ContainableProtocol, LengthableProtocol
from .col_iterable_protocol import IterableProtocol


__all__ = [
    "CollectionProtocol",
]


class CollectionProtocol[ElementT, ResultT](
    ContainableProtocol[ElementT],
    LengthableProtocol,
    IterableProtocol[ElementT, ResultT],
    Protocol,
):
    """Protocol for collection values — like collections.abc.Collection."""

    ...
