# ruff: noqa: D102
"""Item-level capability bases — load, store, erase, exists for items in collections.

ItemGettableBase: .load() wrapping ItemGetOp
ItemSettableBase: .store(value) wrapping ItemSetCmd
ItemDeletableBase: .erase() wrapping ItemDeleteCmd
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
    "ItemGettableBase",
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


class ItemGettableBase[ValueT]:
    """Base for item refs that can read their value.

    Provides load() using ItemGetOp, returning a typed Value wrapper.
    Override result() to customize the Value wrapper (e.g. domain types).
    """

    value_type: type[ValueT]

    def result(self, op: Term) -> object:
        from everybase.abc import typed_value

        return typed_value(self.value_type, op)

    @overload
    def load(self: ItemGettableBase[int]) -> IntValue: ...

    @overload
    def load(self: ItemGettableBase[str]) -> StrValue: ...

    @overload
    def load(self: ItemGettableBase[bool]) -> BoolValue: ...

    @overload
    def load(self: ItemGettableBase[float]) -> FloatValue: ...

    @overload
    def load(self: ItemGettableBase[bytes]) -> BytesValue: ...

    @overload
    def load(self: ItemGettableBase[None]) -> NoneValue: ...

    @overload
    def load[V](self: ItemGettableBase[list[V]]) -> ListValue[V]: ...

    @overload
    def load[K, V](self: ItemGettableBase[dict[K, V]]) -> DictValue[K, V]: ...

    @overload
    def load[V](self: ItemGettableBase[set[V]]) -> SetValue[V]: ...

    def load(self) -> object:
        from everybase.shape.morphisms.item import ItemGetOp

        return self.result(ItemGetOp(self))


class ItemSettableBase[ValueT]:
    """Base for item refs that can write a value.

    Provides store(value) using ItemSetCmd, returning a typed Value wrapper.
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
        from everybase.shape.morphisms.item import ItemSetCmd

        return self.result(ItemSetCmd(self, ensure_term(value)))


class ItemDeletableBase:
    """Base for item refs that can be deleted.

    Provides erase() using ItemDeleteCmd.
    """

    def erase(self) -> NoneValue:
        from everybase.shape.morphisms.item import ItemDeleteCmd

        return NoneValue(ItemDeleteCmd(self))
