"""Query capability bases for LValue references.

This module provides query-related capability bases:
- KeysQueryableBase - for querying keys
- ValuesQueryableBase - for querying values
- ItemsQueryableBase - for querying items (key-value pairs)
"""

from __future__ import annotations

from everybase import ListRef


__all__ = [
    "ItemsQueryableBase",
    "KeysQueryableBase",
    "ValuesQueryableBase",
]


# =============================================================================
# QUERY CAPABILITY BASES
# =============================================================================


class KeysQueryableBase[KeyT]:
    """Implementation base for keys queries.

    Implements the KeysQueryable protocol with keys() method.
    """

    def keys(self) -> ListRef[KeyT]:
        """Create a keys query operation.

        Returns:
            ListRef containing all keys when executed

        Example:
            >>> all_keys = dict_ref.keys().execute(ctx)
        """
        from every_pv.morphisms import KeysOp

        return ListRef(KeysOp(self))


class ValuesQueryableBase[ValueT]:
    """Implementation base for values queries.

    Implements the ValuesQueryable protocol with values() method.
    """

    def values(self) -> ListRef[ValueT]:
        """Create a values query operation.

        Returns:
            ListRef containing all values when executed

        Example:
            >>> all_values = dict_ref.values().execute(ctx)
        """
        from every_pv.morphisms import ValuesOp

        return ListRef(ValuesOp(self))


class ItemsQueryableBase[KeyT, ValueT]:
    """Implementation base for items queries.

    Implements the ItemsQueryable protocol with items() method.
    """

    def items(self) -> ListRef[tuple[KeyT, ValueT]]:
        """Create an items query operation.

        Returns:
            ListRef containing all (key, value) pairs when executed

        Example:
            >>> all_items = dict_ref.items().execute(ctx)
        """
        from every_pv.morphisms import ItemsOp

        return ListRef(ItemsOp(self))
