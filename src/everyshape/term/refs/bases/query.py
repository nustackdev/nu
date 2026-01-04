"""Query capability bases for LValue references.

This module provides query-related capability bases:
- KeysQueryableBase - for querying keys
- ValuesQueryableBase - for querying values
- ItemsQueryableBase - for querying items (key-value pairs)
"""

from __future__ import annotations

from ...comps import (
    ItemsOp,
    KeysOp,
    ValuesOp,
)
from ...values import ListValue


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

    def keys(self) -> ListValue[KeyT]:
        """Create a keys query operation.

        Returns:
            ListValue containing all keys when executed

        Example:
            >>> all_keys = dict_ref.keys().execute(ctx)
        """
        return ListValue(KeysOp(self))


class ValuesQueryableBase[ValueT]:
    """Implementation base for values queries.

    Implements the ValuesQueryable protocol with values() method.
    """

    def values(self) -> ListValue[ValueT]:
        """Create a values query operation.

        Returns:
            ListValue containing all values when executed

        Example:
            >>> all_values = dict_ref.values().execute(ctx)
        """
        return ListValue(ValuesOp(self))


class ItemsQueryableBase[KeyT, ValueT]:
    """Implementation base for items queries.

    Implements the ItemsQueryable protocol with items() method.
    """

    def items(self) -> ListValue[tuple[KeyT, ValueT]]:
        """Create an items query operation.

        Returns:
            ListValue containing all (key, value) pairs when executed

        Example:
            >>> all_items = dict_ref.items().execute(ctx)
        """
        return ListValue(ItemsOp(self))
