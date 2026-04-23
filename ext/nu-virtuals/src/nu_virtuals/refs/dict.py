# ruff: noqa: D102
"""PV mapping reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import (
    AnyI,
    BoolI,
    BytesI,
    DictI,
    DictItemsI,
    DictKeysI,
    DictValuesI,
    FloatI,
    IntI,
    IteratorI,
    ListI,
    SetI,
    StrI,
    ensure_nu,
)
from nu.shapes import ReactiveMappingRef, Shape, Slot
from nu.terms import Mode
from virtuals.collections import MutableMappingBase

from .base import ViewRef
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Interface, Nu, Sentinel
    from virtuals.loc import path


def _value_type_for(python_type: type) -> type[Interface]:
    """Map Python type to its corresponding Interface."""
    mapping: dict[type, type] = {
        int: IntI,
        str: StrI,
        float: FloatI,
        bool: BoolI,
        bytes: BytesI,
        list: ListI,
        dict: DictI,
        set: SetI,
    }
    return mapping.get(python_type, AnyI)


__all__ = [
    "DictRef",
]

from virtuals.types import Value as StorageValue  # noqa: E402


class DictRef[
    K: int | str,
    V: StorageValue,
](
    ReactiveMappingRef[
        K,
        V,
        DictI[K, V],
        AnyI,
    ],
    ViewRef[
        dict[K, V],
        MutableMappingBase,
    ],
):
    """PV mapping reference — document model + PV substrate.

    Operations work lazily on PV views without loading into memory.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def result(self, op: Nu) -> DictI[K, V]:
        return DictI(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysI:
        return DictKeysI(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesI:
        return DictValuesI(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsI:
        return DictItemsI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorI:
        return IteratorI(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        value_type: type[V],
        key_type: type[K],
        view_type: type[MutableMappingBase],
        key_value_type: type,
        value_value_type: type,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize mapping reference."""
        super().__init__(
            address=address, view_type=view_type, parent=parent, owner_shape=owner_shape
        )
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def _create_child_ref(self, key: K | Sentinel | Nu[K | Sentinel]) -> ItemRef:
        """Create a reference to a child at the given key."""
        return ItemRef(
            address=ensure_nu(key),
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot[DK: (int, str), DV: StorageValue](
        cls,
        value_type: type[DV],
        view_type: type[MutableMappingBase] | None = None,
        key_type: type[DK] = str,  # type: ignore[assignment]
    ) -> DictRef[DK, DV]:
        """Create a slot for this dict ref type.

        Args:
            value_type: Python type of values (primitives)
            view_type: View class implementing MutableMappingBase protocol
            key_type: Python type of keys (default: str)

        Returns:
            Slot configured to create DictRef instances
        """
        from virtuals.views import DictView

        return Slot(
            cls,
            value_type=value_type,
            key_type=key_type,
            view_type=view_type or DictView,
            key_value_type=_value_type_for(key_type),
            value_value_type=_value_type_for(value_type),
        )  # type: ignore
