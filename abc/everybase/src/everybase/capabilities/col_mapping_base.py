"""Mapping capability base — Collection + keys/values/items/get.

Follows Python's collections.abc.Mapping pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .col_collection_base import CollectionBase


if TYPE_CHECKING:
    from everyabc import Term


__all__ = [
    "MappingBase",
]


class MappingBase[KeyT, ValueT, ResultT](
    CollectionBase[KeyT, ResultT],
):
    """Base for mapping values — like collections.abc.Mapping."""

    def _wrap_keys_result(self, operand: Term) -> Term:
        """Override in subclass to wrap keys sequence result."""
        raise NotImplementedError()

    def _wrap_values_result(self, operand: Term) -> Term:
        """Override in subclass to wrap values sequence result."""
        raise NotImplementedError()

    def _wrap_items_result(self, operand: Term) -> Term:
        """Override in subclass to wrap items sequence result."""
        raise NotImplementedError()

    def _wrap_value_result(self, operand: Term) -> Term:
        """Override in subclass to wrap single value result."""
        raise NotImplementedError()

    def keys_(self) -> ResultT:
        """Get all keys."""
        from everybase.morphisms.abc_mapping import KeysOp

        return cast("ResultT", self._wrap_keys_result(KeysOp(self)))

    def values_(self) -> ResultT:
        """Get all values."""
        from everybase.morphisms.abc_mapping import ValuesOp

        return cast("ResultT", self._wrap_values_result(ValuesOp(self)))

    def items_(self) -> ResultT:
        """Get all key-value pairs."""
        from everybase.morphisms.abc_mapping import ItemsOp

        return cast("ResultT", self._wrap_items_result(ItemsOp(self)))

    def get_(self, key: KeyT, default: ValueT | None = None) -> ResultT:
        """Get value with default."""
        from everybase.morphisms.abc_mapping import GetOp

        return cast("ResultT", self._wrap_value_result(GetOp(self, key, default)))
