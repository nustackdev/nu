"""Ref implementations.

This module provides ready-to-use ref classes for primitive (leaf) values.

Usage:
    class MyShape(Shape):
        name = StrSlot()
        age = IntSlot()

    # Create operations
    MyShape.name.get()          # GetOp[str] -> StrType
    MyShape.name.set("Alice")   # SetCmd[str] -> StrType
    MyShape.name.remove()       # DeleteCmd -> NoneValue
    MyShape.name.exists()       # ExistsOp -> BoolType
    MyShape.name.on_change()    # OnPrimitiveChangeOp -> Subscription
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyterm.shape import Shape
from everyterm.term import Ref, RValue
from everyterm.types import (
    BoolType,
    BytesType,
    FloatType,
    IntType,
    StrType,
)

from .bases_primitive import (
    CollectionItemRefBase,
    MutableMappingItemRefBase,
    MutableSequenceItemRefBase,
)
from .ref import PrimitiveRef


if TYPE_CHECKING:
    from pv.loc import path


__all__ = [
    "ItemRef",
    "ListItemRef",
    "DictItemRef",
    # Basic type aliases
    "IntRef",
    "StrRef",
    "FloatRef",
    "BoolRef",
    "BytesRef",
]


class ItemRef[T, ValueT](CollectionItemRefBase[T, ValueT], PrimitiveRef[T]):
    """Complete implementation for primitive value references.

    Combines ValueRefBase capabilities with PrimitiveRef:
    - exists(), missing() from ExistableBase
    - get() from GettableBase
    - set() from SettableBase
    - remove() from DeletableBase
    - on_change() from PrimitiveObservableBase

    Implements CollectionItemRef protocol from collections.py.

    Type Parameters:
        T: Native Python type at this location (int, str, float, bool, etc.)
        ValueT: Type type for this value (IntType, StrType, etc.)

    Example:
        # Usage via slots
        name_ref = shape.name
        get_op = name_ref.get()      # Returns StrType
        set_cmd = name_ref.set("x")  # Returns StrType
        del_cmd = name_ref.remove()  # Returns NoneValue
        exists = name_ref.exists()   # Returns BoolType
        sub_op = name_ref.on_change() # Returns OnPrimitiveChangeOp
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent_ref: Ref | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize item reference.

        Args:
            address: Address of this field in parent's domain
            value_type: Native Python type for the value
            value_value_type: Type type for the value
            parent_ref: Parent reference in navigation chain
            owner_shape: Shape class this ref belongs to
        """
        super().__init__(address, value_type, parent_ref, owner_shape)
        self.value_value_type = value_value_type


class ListItemRef[T, ValueT](MutableSequenceItemRefBase[T, ValueT], PrimitiveRef[T]):
    """Reference to a primitive value that is a child of a list.

    Used for individual items in a list container where items are
    primitive values (not nested structures).

    Same capabilities as ItemRef - the distinction is semantic and
    helps with type clarity when building refs for sequence items.

    Type Parameters:
        T: Native Python type at this location (int, str, float, etc.)
        ValueT: Type type for this value (IntType, StrType, etc.)

    Example:
        # Usage
        numbers = shape.numbers  # ListRef
        first = numbers[0]       # ListItemRef[int, IntType]
        first.get()              # GetOp -> IntType
        first.set(42)            # SetCmd -> IntType
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent_ref: Ref | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize list item reference.

        Args:
            address: Index in the parent list
            value_type: Native Python type for the value
            value_value_type: Type type for the value
            parent_ref: Parent reference (the list ref)
            owner_shape: Shape class this ref belongs to
        """
        super().__init__(address, value_type, parent_ref, owner_shape)
        self.value_value_type = value_value_type


class DictItemRef[T, ValueT](MutableMappingItemRefBase[T, ValueT], PrimitiveRef[T]):
    """Reference to a primitive value that is a child of a mapping.

    Same operations as ItemRef since primitive value operations
    (get, set, remove) work through the parent view regardless of mutability.

    The mutability distinction is at the parent mapping level, not the
    individual value level. This class exists for type system clarity.

    Type Parameters:
        T: Native Python type at this location (int, str, float, etc.)
        ValueT: Type type for this value (IntType, StrType, etc.)

    Example:
        # Usage
        scores = shape.scores  # DictRef
        score = scores["alice"]  # DictItemRef[int, IntType]
        score.get()              # GetOp -> IntType
        score.set(100)           # SetCmd -> IntType
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent_ref: Ref | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize dict item reference.

        Args:
            address: Key in the parent dict
            value_type: Native Python type for the value
            value_value_type: Type type for the value
            parent_ref: Parent reference (the dict ref)
            owner_shape: Shape class this ref belongs to
        """
        super().__init__(address, value_type, parent_ref, owner_shape)
        self.value_value_type = value_value_type


# =====================================================================
# Type Aliases for Common Types
# =====================================================================

# Basic type aliases (ItemRef variants)
type IntRef = ItemRef[int, IntType]
type StrRef = ItemRef[str, StrType]
type FloatRef = ItemRef[float, FloatType]
type BoolRef = ItemRef[bool, BoolType]
type BytesRef = ItemRef[bytes, BytesType]
