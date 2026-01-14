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
from ...types import NilType
from ...types.conversion import literal


if TYPE_CHECKING:
    from everyshape.typing import Sentinel

    from ...term import Term


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

    def add(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NilType:
        """Create an add command.

        Args:
            value: Item to add (literal or Term)

        Returns:
            NilType (add returns None after execution)

        Example:
            >>> set_ref.add("item").execute(ctx)
        """
        return NilType(AddValueCmd(self, literal(value)))


class SetRemovableBase[ItemT]:
    """Implementation base for removing from sets.

    Implements remove() and discard() methods for sets.
    """

    def remove(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NilType:
        """Create a remove command.

        Args:
            value: Item to remove (literal or Term)

        Returns:
            NilType (remove returns None after execution)

        Note:
            Raises KeyError at execution if item not found.

        Example:
            >>> set_ref.remove("item").execute(ctx)
        """
        return NilType(RemoveValueCmd(self, literal(value)))

    def discard(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NilType:
        """Create a discard command.

        Args:
            value: Item to discard (literal or Term)

        Returns:
            NilType (discard returns None after execution, no error if missing)

        Example:
            >>> set_ref.discard("item").execute(ctx)  # No error if missing
        """
        return NilType(DiscardValueCmd(self, literal(value)))
