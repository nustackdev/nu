# ruff: noqa: D102
"""PV mapping reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pv.collections import MutableMappingView

from everybase import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    ListValue,
    SetValue,
    StrValue,
    ensure_term,
)
from everyshape import ReactiveMappingRefBase, Shape, Slot

from .base import ViewRef
from .items import ItemRef


if TYPE_CHECKING:
    from pv.loc import path

    from everyabc import Sentinel, Term, Value


def _value_type_for(python_type: type) -> type[Value]:
    """Map Python type to its corresponding Value type."""
    mapping: dict[type, type] = {
        int: IntValue,
        str: StrValue,
        float: FloatValue,
        bool: BoolValue,
        bytes: BytesValue,
        list: ListValue,
        dict: DictValue,
        set: SetValue,
    }
    return mapping.get(python_type, AnyValue)


__all__ = [
    "DictRef",
]

from pv.types import Value as StorageValue  # noqa: E402


class DictRef[
    K: int | str,
    V: StorageValue,
](
    ReactiveMappingRefBase[
        K,
        V,
        DictValue[K, V],
        AnyValue,
    ],
    ViewRef[
        dict[K, V],
        MutableMappingView,
    ],
):
    """PV mapping reference — document model + PV substrate.

    Operations work lazily on PV views without loading into memory.
    """

    def result(self, op: Term) -> DictValue[K, V]:
        return DictValue(op)

    def _wrap_keys_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_values_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_items_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_value_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[V],
        key_type: type[K],
        view_type: type[MutableMappingView],
        key_value_type: type,
        value_value_type: type,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize mapping reference."""
        super().__init__(address, view_type, parent, owner_shape)
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ItemRef:
        """Create a reference to a child at the given key."""
        return ItemRef(
            address=ensure_term(key),
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot(
        cls,
        value_type: type[V],
        view_type: type[MutableMappingView] | None = None,
        key_type: type[K] = str,
    ) -> Self:
        """Create a slot for this dict ref type.

        Args:
            value_type: Python type of values (primitives)
            view_type: View class implementing MutableMappingView protocol
            key_type: Python type of keys (default: str)

        Returns:
            Slot configured to create DictRef instances
        """
        from every_pv.views import DictView

        return Slot(
            cls,
            value_type=value_type,
            key_type=key_type,
            view_type=view_type or DictView,
            key_value_type=_value_type_for(key_type),
            value_value_type=_value_type_for(value_type),
        )  # type: ignore
