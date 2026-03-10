# ruff: noqa: D102
"""Item-level capability bases — store, erase, exists for items in collections.

Refs ARE terms — executing a ref reads its value (via fetch/coerce).
No separate load() needed. The ref itself is the readable term.

ItemSettableBase: .store(value) wrapping ItemStoreCmd
ItemDeletableBase: .erase() wrapping ItemEraseCmd
ItemExistableBase: .exists(), .missing()

These bases are for refs that represent items within a collection.
The ref must implement fetch_parent(ctx) and resolve_address(ctx).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everybase.abc import (
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    ListValue,
    NoneValue,
    SetValue,
    StrValue,
)


if TYPE_CHECKING:
    from everybase import Sentinel, Term


__all__ = [
    "ItemDeletableBase",
    "ItemExistableBase",
    "ItemSettableBase",
]


class ItemExistableBase:
    """Base for item refs that can check existence.

    Provides exists() and missing() using ItemExistsOp/ItemMissingOp.
    """

    def exists(self) -> BoolValue:
        from everybase.shape.morphisms.item import ItemExistsOp

        return BoolValue(ItemExistsOp(self))

    def missing(self) -> BoolValue:
        from everybase.shape.morphisms.item import ItemMissingOp

        return BoolValue(ItemMissingOp(self))


class ItemSettableBase[ValueT]:
    """Base for item refs that can write a value.

    Provides store(value) using ItemStoreCmd, returning a typed Value wrapper.
    Override result() to customize the Value wrapper (e.g. domain types).
    """

    value_type: type[ValueT]

    def result(self, op: Term) -> object:
        from everybase.abc import typed_value

        return typed_value(self.value_type, op)

    @overload
    def store(
        self: ItemSettableBase[int], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> IntValue: ...

    @overload
    def store(
        self: ItemSettableBase[str], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> StrValue: ...

    @overload
    def store(
        self: ItemSettableBase[bool], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> BoolValue: ...

    @overload
    def store(
        self: ItemSettableBase[float], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> FloatValue: ...

    @overload
    def store(
        self: ItemSettableBase[bytes], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> BytesValue: ...

    @overload
    def store(
        self: ItemSettableBase[None], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> NoneValue: ...

    @overload
    def store[V](
        self: ItemSettableBase[list[V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> ListValue[V]: ...

    @overload
    def store[K, V](
        self: ItemSettableBase[dict[K, V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> DictValue[K, V]: ...

    @overload
    def store[V](
        self: ItemSettableBase[set[V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> SetValue[V]: ...

    def store(self, value: ValueT | Sentinel | Term[ValueT | Sentinel]) -> object:
        from everybase.abc import ensure_term
        from everybase.shape.morphisms.item import ItemStoreCmd

        return self.result(ItemStoreCmd(self, ensure_term(value)))


class ItemDeletableBase:
    """Base for item refs that can be deleted.

    Provides erase() using ItemEraseCmd.
    """

    def erase(self) -> NoneValue:
        from everybase.shape.morphisms.item import ItemEraseCmd

        return NoneValue(ItemEraseCmd(self))
