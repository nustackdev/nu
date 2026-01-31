"""Slot implementations for dict substrate.

Provides slot types that create dict-substrate refs:
- ItemSlot: creates ItemRef for primitive values
- DictSlot: creates MappingRef for dict-like collections
- ListSlot: creates SequenceRef for list-like collections
- ShapeSlot: creates ShapeRef for nested shapes
- ShapesListSlot: creates ShapesListRef
- ShapesDictSlot: creates ShapesDictRef
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from every_dict.collections import (
    MappingRef,
    SequenceRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
)
from every_dict.items import ItemRef
from everyabc import Slot, Value
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
)


if TYPE_CHECKING:
    from everyabc import Ref
    from everyshape import ShapeBase


def _value_type_for(python_type: type) -> type[Value]:
    """Map Python type to its corresponding Value type."""
    mapping: dict[type, type[Value]] = {
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
    "BoolSlot",
    "BytesSlot",
    "DictSlot",
    "FloatSlot",
    "IntSlot",
    "ItemSlot",
    "ListSlot",
    "ShapeSlot",
    "ShapesDictSlot",
    "ShapesListSlot",
    "StrSlot",
]


# =============================================================================
# ITEM SLOT
# =============================================================================


class _ItemSlot(Slot):
    """Slot that creates ItemRef for primitive values."""

    def __init__(self, value_type: type, value_value_type: type) -> None:
        """Initialize item slot."""
        super().__init__()
        self.value_type = value_type
        self.value_value_type = value_value_type

    def create_ref(
        self,
        owner_shape: type[ShapeBase],
        parent_ref: Ref | None = None,
    ) -> ItemRef:
        """Create ItemRef for this slot."""
        return ItemRef(
            address=self.name,
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def ItemSlot(value_type: type, value_value_type: type) -> ItemRef:  # noqa: N802
    """Create a slot for primitive values.

    Args:
        value_type: Python type of the value (int, str, float, etc.)
        value_value_type: Value wrapper type (IntValue, StrValue, etc.)

    Returns:
        Slot instance.
    """
    return _ItemSlot(value_type=value_type, value_value_type=value_value_type)  # type: ignore


# =============================================================================
# DICT SLOT
# =============================================================================


class _DictSlot(Slot):
    """Slot that creates MappingRef."""

    def __init__(self, value_type: type, key_type: type = str) -> None:
        """Initialize dict slot."""
        super().__init__()
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = _value_type_for(key_type)
        self.value_value_type = _value_type_for(value_type)

    def create_ref(
        self,
        owner_shape: type[ShapeBase],
        parent_ref: Ref | None = None,
    ) -> MappingRef:
        """Create MappingRef for this slot."""
        return MappingRef(
            address=self.name,
            value_type=self.value_type,
            key_type=self.key_type,
            key_value_type=self.key_value_type,
            value_value_type=self.value_value_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def DictSlot(value_type: type, key_type: type = str) -> MappingRef:  # noqa: N802
    """Create a slot for dict-like collections.

    Args:
        value_type: Python type of values
        key_type: Python type of keys (default: str)

    Returns:
        Slot instance.
    """
    return _DictSlot(value_type=value_type, key_type=key_type)  # type: ignore


# =============================================================================
# LIST SLOT
# =============================================================================


class _ListSlot(Slot):
    """Slot that creates SequenceRef."""

    def __init__(self, item_type: type) -> None:
        """Initialize list slot."""
        super().__init__()
        self.item_type = item_type
        self.item_value_type = _value_type_for(item_type)

    def create_ref(
        self,
        owner_shape: type[ShapeBase],
        parent_ref: Ref | None = None,
    ) -> SequenceRef:
        """Create SequenceRef for this slot."""
        return SequenceRef(
            address=self.name,
            item_type=self.item_type,
            item_value_type=self.item_value_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def ListSlot(item_type: type) -> SequenceRef:  # noqa: N802
    """Create a slot for list-like collections.

    Args:
        item_type: Python type of items

    Returns:
        Slot instance.
    """
    return _ListSlot(item_type=item_type)  # type: ignore


# =============================================================================
# SHAPE SLOT
# =============================================================================


class _ShapeSlot(Slot):
    """Slot that creates ShapeRef for nested shapes."""

    def __init__(self, shape_type: type) -> None:
        """Initialize shape slot."""
        super().__init__()
        self.shape_type = shape_type

    def create_ref(
        self,
        owner_shape: type[ShapeBase],
        parent_ref: Ref | None = None,
    ) -> ShapeRef:
        """Create ShapeRef for this slot."""
        return ShapeRef(
            address=self.name,
            shape_type=self.shape_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def ShapeSlot(shape_type: type) -> ShapeRef:  # noqa: N802
    """Create a slot for nested shapes.

    Args:
        shape_type: Shape class for the nested structure

    Returns:
        Slot instance.
    """
    return _ShapeSlot(shape_type=shape_type)  # type: ignore


# =============================================================================
# SHAPES LIST SLOT
# =============================================================================


class _ShapesListSlot(Slot):
    """Slot that creates ShapesListRef."""

    def __init__(self, shape_type: type) -> None:
        """Initialize shapes list slot."""
        super().__init__()
        self.shape_type = shape_type

    def create_ref(
        self,
        owner_shape: type[ShapeBase],
        parent_ref: Ref | None = None,
    ) -> ShapesListRef:
        """Create ShapesListRef for this slot."""
        return ShapesListRef(
            address=self.name,
            shape_type=self.shape_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def ShapesListSlot(shape_type: type) -> ShapesListRef:  # noqa: N802
    """Create a slot for lists of shapes.

    Args:
        shape_type: Shape class for items

    Returns:
        Slot instance.
    """
    return _ShapesListSlot(shape_type=shape_type)  # type: ignore


# =============================================================================
# SHAPES DICT SLOT
# =============================================================================


class _ShapesDictSlot(Slot):
    """Slot that creates ShapesDictRef."""

    def __init__(self, shape_type: type, key_type: type = str) -> None:
        """Initialize shapes dict slot."""
        super().__init__()
        self.shape_type = shape_type
        self.key_type = key_type
        self.key_value_type = _value_type_for(key_type)

    def create_ref(
        self,
        owner_shape: type[ShapeBase],
        parent_ref: Ref | None = None,
    ) -> ShapesDictRef:
        """Create ShapesDictRef for this slot."""
        return ShapesDictRef(
            address=self.name,
            key_type=self.key_type,
            key_value_type=self.key_value_type,
            shape_type=self.shape_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def ShapesDictSlot(shape_type: type, key_type: type = str) -> ShapesDictRef:  # noqa: N802
    """Create a slot for dicts of shapes.

    Args:
        shape_type: Shape class for values
        key_type: Python type for keys (default: str)

    Returns:
        Slot instance.
    """
    return _ShapesDictSlot(shape_type=shape_type, key_type=key_type)  # type: ignore


# =============================================================================
# CONVENIENCE ALIASES
# =============================================================================


def IntSlot() -> ItemRef[int, IntValue]:  # noqa: N802
    """Create a slot for int values."""
    return ItemSlot(int, IntValue)  # type: ignore


def StrSlot() -> ItemRef[str, StrValue]:  # noqa: N802
    """Create a slot for str values."""
    return ItemSlot(str, StrValue)  # type: ignore


def FloatSlot() -> ItemRef[float, FloatValue]:  # noqa: N802
    """Create a slot for float values."""
    return ItemSlot(float, FloatValue)  # type: ignore


def BoolSlot() -> ItemRef[bool, BoolValue]:  # noqa: N802
    """Create a slot for bool values."""
    return ItemSlot(bool, BoolValue)  # type: ignore


def BytesSlot() -> ItemRef[bytes, BytesValue]:  # noqa: N802
    """Create a slot for bytes values."""
    return ItemSlot(bytes, BytesValue)  # type: ignore
