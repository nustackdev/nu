# ruff: noqa: D102
"""Mapping capability — protocols + bases + mutations.

MappingProtocol/Base = Collection + keys_/values_/items_/get_
MutableMappingProtocol/Base = Mapping + set_/delete/update_

Follows Python's collections.abc.Mapping / MutableMapping pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from .col_collection import CollectionBase, CollectionProtocol


if TYPE_CHECKING:
    from collections.abc import Mapping

    from everyabc import Term


__all__ = [
    "MappingBase",
    "MappingProtocol",
    "MutableMappingBase",
    "MutableMappingProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


class MappingProtocol[KeyT, ValueT, ResultT](
    CollectionProtocol[KeyT, ResultT],
    Protocol,
):
    """Protocol for mapping values — like collections.abc.Mapping."""

    def keys_(self) -> ResultT: ...
    def values_(self) -> ResultT: ...
    def items_(self) -> ResultT: ...
    def get_(self, key: KeyT, default: ValueT | None = None) -> ResultT: ...


class MutableMappingProtocol[KeyT, ValueT, ResultT](
    MappingProtocol[KeyT, ValueT, ResultT],
    Protocol,
):
    """Protocol for mutable mapping values — like collections.abc.MutableMapping."""

    def set_(self, key: KeyT, value: ValueT) -> ResultT: ...
    def delete(self, key: KeyT) -> ResultT: ...
    def update_(self, other: Mapping[KeyT, ValueT]) -> ResultT: ...


# =============================================================================
# BASES
# =============================================================================


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


class MutableMappingBase[KeyT, ValueT, ResultT](
    MappingBase[KeyT, ValueT, ResultT],
):
    """Base for mutable mapping values — like collections.abc.MutableMapping."""

    def set_(self, key: KeyT, value: ValueT) -> ResultT:
        """Set value at key."""
        from everybase.morphisms.abc_mapping import SetItemCmd

        return cast("ResultT", self._wrap_value_result(SetItemCmd(self, key, value)))

    def delete(self, key: KeyT) -> ResultT:
        """Delete entry by key."""
        from everybase.morphisms.abc_mapping import DeleteItemCmd

        return cast("ResultT", self._wrap_value_result(DeleteItemCmd(self, key)))

    def update_(self, other: Mapping[KeyT, ValueT]) -> ResultT:
        """Update mapping with another mapping."""
        from everybase.morphisms.abc_mapping import UpdateCmd

        return cast("ResultT", self._wrap_value_result(UpdateCmd(self, other)))
