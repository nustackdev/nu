"""Collection capability base — Containable + Lengthable + Iterable.

Follows Python's collections.abc.Collection pattern.
"""

from __future__ import annotations

from .col_atoms_base import ContainableBase, LengthableBase
from .col_iterable_base import IterableBase


__all__ = [
    "CollectionBase",
]


class CollectionBase[ElementT, ResultT](
    ContainableBase[ElementT],
    LengthableBase,
    IterableBase[ElementT, ResultT],
):
    """Base for collection values — like collections.abc.Collection."""

    pass
