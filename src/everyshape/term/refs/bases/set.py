"""Set capability bases for LValue references.

This module provides set-related capability bases:
- SetAddableBase - for adding items to sets
- SetRemovableBase - for removing items from sets
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...comps.ref import (
    AddValueCmd,
    DiscardValueCmd,
    RemoveValueCmd,
)
from ...values import NoneValue
from ...values.conversion import literal


if TYPE_CHECKING:
    from everyshape.typing import Sentinel

    from ...term import RValue


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

    def add(self, value: ItemT | Sentinel | RValue[ItemT | Sentinel]) -> NoneValue:
        """Create an add command.

        Args:
            value: Item to add (literal or RValue)

        Returns:
            NoneValue (add returns None after execution)

        Example:
            >>> set_ref.add("item").execute(ctx)
        """
        return NoneValue(AddValueCmd(self, literal(value)))


class SetRemovableBase[ItemT]:
    """Implementation base for removing from sets.

    Implements remove() and discard() methods for sets.
    """

    def remove(self, value: ItemT | Sentinel | RValue[ItemT | Sentinel]) -> NoneValue:
        """Create a remove command.

        Args:
            value: Item to remove (literal or RValue)

        Returns:
            NoneValue (remove returns None after execution)

        Note:
            Raises KeyError at execution if item not found.

        Example:
            >>> set_ref.remove("item").execute(ctx)
        """
        return NoneValue(RemoveValueCmd(self, literal(value)))

    def discard(self, value: ItemT | Sentinel | RValue[ItemT | Sentinel]) -> NoneValue:
        """Create a discard command.

        Args:
            value: Item to discard (literal or RValue)

        Returns:
            NoneValue (discard returns None after execution, no error if missing)

        Example:
            >>> set_ref.discard("item").execute(ctx)  # No error if missing
        """
        return NoneValue(DiscardValueCmd(self, literal(value)))
