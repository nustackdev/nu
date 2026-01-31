# ruff: noqa: D102
"""Collection + Clearable capabilities — protocols + bases.

CollectionProtocol/Base = Containable + Lengthable + Iterable
ClearableProtocol/Base = clear()

Follows Python's collections.abc.Collection pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .col_atoms import ContainableBase, ContainableProtocol, LengthableBase, LengthableProtocol
from .col_iterable import IterableBase, IterableProtocol


if TYPE_CHECKING:
    from everybase.values import AnyValue


__all__ = [
    "ClearableBase",
    "ClearableProtocol",
    "CollectionBase",
    "CollectionProtocol",
]


# =============================================================================
# COLLECTION
# =============================================================================


class CollectionProtocol[ElementT, ResultT](
    ContainableProtocol[ElementT],
    LengthableProtocol,
    IterableProtocol[ElementT, ResultT],
    Protocol,
):
    """Protocol for collection values — like collections.abc.Collection."""

    ...


class CollectionBase[ElementT, ResultT](
    ContainableBase[ElementT],
    LengthableBase,
    IterableBase[ElementT, ResultT],
):
    """Base for collection values — like collections.abc.Collection."""

    pass


# =============================================================================
# CLEARABLE
# =============================================================================


class ClearableProtocol(Protocol):
    """Protocol for clearable collections."""

    def clear(self) -> None: ...


class ClearableBase:
    """Base for clearable collections."""

    def clear(self) -> AnyValue:
        """Clear all items from this collection."""
        from everybase.morphisms.cmd_collection import ClearCmd
        from everybase.values import AnyValue

        return AnyValue(ClearCmd(self))
