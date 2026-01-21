"""Set capability bases for LValue references.

This module provides set-related capability bases:
- SetAddableBase - for adding items to sets
- SetRemovableBase - for removing items from sets
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.conversion import literal
from everybase.types import NoneType

from ..comp import (
    AddValueCmd,
    DiscardValueCmd,
    RemoveValueCmd,
)


if TYPE_CHECKING:
    from every import Sentinel, Term


__all__ = [
    "SetAddableBase",
    "SetRemovableBase",
]


# =============================================================================
# SET CAPABILITY BASES
# =============================================================================


class SetAddableBase[ItemT]:
    """Implementation base for adding to sets.

    Implements add() method for sets.
    """

    def add(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NoneType:
        """Create an add command.

        Args:
            value: Item to add (literal or Term)

        Returns:
            NoneType (add returns None after execution)

        Example:
            >>> set_ref.add("item").execute(ctx)
        """
        return NoneType(AddValueCmd(self, literal(value)))


class SetRemovableBase[ItemT]:
    """Implementation base for removing from sets.

    Implements remove() and discard() methods for sets.
    """

    def remove(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NoneType:
        """Create a remove command.

        Args:
            value: Item to remove (literal or Term)

        Returns:
            NoneType (remove returns None after execution)

        Note:
            Raises KeyError at execution if item not found.

        Example:
            >>> set_ref.remove("item").execute(ctx)
        """
        return NoneType(RemoveValueCmd(self, literal(value)))

    def discard(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NoneType:
        """Create a discard command.

        Args:
            value: Item to discard (literal or Term)

        Returns:
            NoneType (discard returns None after execution, no error if missing)

        Example:
            >>> set_ref.discard("item").execute(ctx)  # No error if missing
        """
        return NoneType(DiscardValueCmd(self, literal(value)))
