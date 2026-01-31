"""Set capability bases for LValue references.

This module provides set-related capability bases:
- SetAddableBase - for adding items to sets
- SetRemovableBase - for removing items from sets
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import NoneValue, ensure_term


if TYPE_CHECKING:
    from everyabc import Sentinel, Term


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

    def add(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NoneValue:
        """Create an add command.

        Args:
            value: Item to add (literal or Term)

        Returns:
            NoneValue (add returns None after execution)

        Example:
            >>> set_ref.add("item").execute(ctx)
        """
        from every_pv.morphisms import AddValueCmd

        return NoneValue(AddValueCmd(self, ensure_term(value)))


class SetRemovableBase[ItemT]:
    """Implementation base for removing from sets.

    Implements remove() and discard() methods for sets.
    """

    def remove(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NoneValue:
        """Create a remove command.

        Args:
            value: Item to remove (literal or Term)

        Returns:
            NoneValue (remove returns None after execution)

        Note:
            Raises KeyError at execution if item not found.

        Example:
            >>> set_ref.remove("item").execute(ctx)
        """
        from every_pv.morphisms import RemoveValueCmd

        return NoneValue(RemoveValueCmd(self, ensure_term(value)))

    def discard(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NoneValue:
        """Create a discard command.

        Args:
            value: Item to discard (literal or Term)

        Returns:
            NoneValue (discard returns None after execution, no error if missing)

        Example:
            >>> set_ref.discard("item").execute(ctx)  # No error if missing
        """
        from every_pv.morphisms import DiscardValueCmd

        return NoneValue(DiscardValueCmd(self, ensure_term(value)))
