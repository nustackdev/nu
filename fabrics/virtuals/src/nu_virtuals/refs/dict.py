# ruff: noqa: D102
"""virtuals mapping reference — document model + virtuals substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import (
    AnyForm,
    BoolForm,
    BytesForm,
    DictForm,
    DictItemsForm,
    DictKeysForm,
    DictValuesForm,
    FloatForm,
    IntForm,
    IteratorForm,
    ListForm,
    SetForm,
    StrForm,
)
from nu.shapes import ReactiveMappingRef, Shape, Slot
from nu.terms import Mode
from virtuals.collections import MutableMappingBase

from .base import ViewRef
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Form, Nu, Sentinel
    from virtuals.loc import path


def _value_type_for(python_type: type) -> type[Form]:
    """Map Python type to its corresponding Form."""
    mapping: dict[type, type] = {
        int: IntForm,
        str: StrForm,
        float: FloatForm,
        bool: BoolForm,
        bytes: BytesForm,
        list: ListForm,
        dict: DictForm,
        set: SetForm,
    }
    return mapping.get(python_type, AnyForm)


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
        DictForm[K, V],
        AnyForm,
    ],
    ViewRef[
        dict[K, V],
        MutableMappingBase,
    ],
):
    """virtuals mapping reference — document model + virtuals substrate.

    Operations work lazily on virtuals views without loading into memory.
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def result(self, op: Nu) -> DictForm[K, V]:
        return DictForm(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysForm:
        return DictKeysForm(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesForm:
        return DictValuesForm(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsForm:
        return DictItemsForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorForm:
        return IteratorForm(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

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
            address=key,
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
