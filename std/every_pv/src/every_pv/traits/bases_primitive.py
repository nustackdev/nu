"""Complete reference base implementations for primitives.

This module provides ready-to-extend ref base classes for primitives.

Type Parameters (matching protocol conventions):
    T: Native Python type at this location (int, str, float, nested dict, etc.)
    ValueT: ComputedValue type for this value (IntType, StrType, FloatType, AnyType, etc.)
"""

from __future__ import annotations

from .core import (
    DeletableBase,
    ExistableBase,
    GettableBase,
    SettableBase,
)
from .observable import PrimitiveObservableBase


__all__ = [
    "CollectionItemRefBase",
    "MappingItemRefBase",
    "MutableMappingItemRefBase",
    "MutableSequenceItemRefBase",
    "SequenceItemRefBase",
]


class CollectionItemRefBase[T, ValueT](
    ExistableBase,
    GettableBase[T],
    SettableBase[T],
    DeletableBase,
    PrimitiveObservableBase,
):
    """Combined base for primitive value capabilities.

    Provides all standard primitive ref operations:
    - exists(), missing() from ExistableBase
    - get() from GettableBase
    - set() from SettableBase
    - remove() from DeletableBase
    - on_change() from PrimitiveObservableBase

    Type Parameters:
        T: Native Python type at this location (int, str, float, nested dict, etc.)
        ValueT: ComputedValue type for this value (IntType, StrType, FloatType, AnyType, etc.)

    Example:
        class MyValueRef(CollectionItemRefBase[str, StrType], PrimitiveRef, ABC):
            value_type = str
            value_value_type = StrType
    """

    value_type: type[T]
    value_value_type: type[ValueT]

    pass


class SequenceItemRefBase[T, ValueT](CollectionItemRefBase[T, ValueT]):
    """Base for primitive values that are children of sequences.

    Same capabilities as CollectionItemRefBase. The distinction is semantic
    and helps with type clarity when building refs for sequence items.

    Type Parameters:
        T: Native Python type at this location (int, str, float, nested dict, etc.)
        ValueT: ComputedValue type for this value (IntType, StrType, FloatType, AnyType, etc.)

    Example:
        class MySequenceItemRef(SequenceItemRefBase[int, IntType], PrimitiveRef, ABC):
            value_type = int
            value_value_type = IntType
    """

    pass


class MutableSequenceItemRefBase[T, ValueT](SequenceItemRefBase[T, ValueT]):
    """Mutable variant for sequence item refs.

    Same operations as SequenceItemRefBase since primitive value operations
    (get, set, remove) work through the parent view regardless of mutability.

    Type Parameters:
        T: Native Python type at this location (int, str, float, nested dict, etc.)
        ValueT: ComputedValue type for this value (IntType, StrType, FloatType, AnyType, etc.)
    """

    pass


class MappingItemRefBase[T, ValueT](CollectionItemRefBase[T, ValueT]):
    """Base for primitive values that are children of mappings.

    Same capabilities as CollectionItemRefBase. The distinction is semantic
    and helps with type clarity when building refs for mapping values.

    Type Parameters:
        T: Native Python type at this location (int, str, float, nested dict, etc.)
        ValueT: ComputedValue type for this value (IntType, StrType, FloatType, AnyType, etc.)

    Example:
        class MyMappingValueRef(MappingItemRefBase[str, StrType], PrimitiveRef, ABC):
            value_type = str
            value_value_type = StrType
    """

    pass


class MutableMappingItemRefBase[T, ValueT](MappingItemRefBase[T, ValueT]):
    """Mutable variant for mapping value refs.

    Same operations as MappingItemRefBase since primitive value operations
    (get, set, remove) work through the parent view regardless of mutability.

    Type Parameters:
        T: Native Python type at this location (int, str, float, nested dict, etc.)
        ValueT: ComputedValue type for this value (IntType, StrType, FloatType, AnyType, etc.)
    """

    pass
