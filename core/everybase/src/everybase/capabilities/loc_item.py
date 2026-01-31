# ruff: noqa: D102
"""Item-level capability bases — get, set, delete, exists for items in collections.

ItemGettableBase: .get() wrapping ItemGetOp
ItemSettableBase: .set(value) wrapping ItemSetCmd
ItemDeletableBase: .remove() wrapping ItemDeleteCmd
ItemExistableBase: .exists(), .missing()

These bases are for refs that represent items within a collection.
The ref must implement fetch_parent(ctx) and resolve_address(ctx).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everybase.values import (
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
    from everyabc import Sentinel, Term


__all__ = [
    "ItemDeletableBase",
    "ItemExistableBase",
    "ItemGettableBase",
    "ItemSettableBase",
]


class ItemExistableBase:
    """Base for item refs that can check existence.

    Provides exists() and missing() using ItemExistsOp/ItemMissingOp.
    """

    def exists(self) -> BoolValue:
        from everybase.morphisms.loc_item import ItemExistsOp

        return BoolValue(ItemExistsOp(self))

    def missing(self) -> BoolValue:
        from everybase.morphisms.loc_item import ItemMissingOp

        return BoolValue(ItemMissingOp(self))


class ItemGettableBase[ValueT]:
    """Base for item refs that can read their value.

    Provides get() using ItemGetOp, returning a typed Value wrapper.
    Requires self.value_type attribute.
    """

    value_type: type[ValueT]

    @overload
    def get(self: ItemGettableBase[int]) -> IntValue: ...

    @overload
    def get(self: ItemGettableBase[str]) -> StrValue: ...

    @overload
    def get(self: ItemGettableBase[bool]) -> BoolValue: ...

    @overload
    def get(self: ItemGettableBase[float]) -> FloatValue: ...

    @overload
    def get(self: ItemGettableBase[bytes]) -> BytesValue: ...

    @overload
    def get(self: ItemGettableBase[None]) -> NoneValue: ...

    @overload
    def get[V](self: ItemGettableBase[list[V]]) -> ListValue[V]: ...

    @overload
    def get[K, V](self: ItemGettableBase[dict[K, V]]) -> DictValue[K, V]: ...

    @overload
    def get[V](self: ItemGettableBase[set[V]]) -> SetValue[V]: ...

    def get(self) -> object:
        from everybase.morphisms.loc_item import ItemGetOp
        from everybase.utils import typed_value

        return typed_value(self.value_type, ItemGetOp(self))


class ItemSettableBase[ValueT]:
    """Base for item refs that can write a value.

    Provides set(value) using ItemSetCmd, returning a typed Value wrapper.
    Requires self.value_type attribute.
    """

    value_type: type[ValueT]

    @overload
    def set(
        self: ItemSettableBase[int], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> IntValue: ...

    @overload
    def set(
        self: ItemSettableBase[str], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> StrValue: ...

    @overload
    def set(
        self: ItemSettableBase[bool], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> BoolValue: ...

    @overload
    def set(
        self: ItemSettableBase[float], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> FloatValue: ...

    @overload
    def set(
        self: ItemSettableBase[bytes], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> BytesValue: ...

    @overload
    def set(
        self: ItemSettableBase[None], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> NoneValue: ...

    @overload
    def set[V](
        self: ItemSettableBase[list[V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> ListValue[V]: ...

    @overload
    def set[K, V](
        self: ItemSettableBase[dict[K, V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> DictValue[K, V]: ...

    @overload
    def set[V](
        self: ItemSettableBase[set[V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> SetValue[V]: ...

    def set(self, value: ValueT | Sentinel | Term[ValueT | Sentinel]) -> object:
        from everybase.morphisms.loc_item import ItemSetCmd
        from everybase.utils import ensure_term, typed_value

        return typed_value(self.value_type, ItemSetCmd(self, ensure_term(value)))


class ItemDeletableBase:
    """Base for item refs that can be deleted.

    Provides remove() using ItemDeleteCmd.
    """

    def remove(self) -> NoneValue:
        from everybase.morphisms.loc_item import ItemDeleteCmd

        return NoneValue(ItemDeleteCmd(self))
