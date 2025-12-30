"""Complete reference base implementations for primitives.

This module provides ready-to-extend ref base classes for primitives.
"""

from __future__ import annotations

from .bases import (
    DeletableBase,
    ExistableBase,
    GettableBase,
    PrimitiveObservableBase,
    SettableBase,
)


__all__ = [
    "MappingValueRefBase",
    "MutableMappingValueRefBase",
    "MutableSequenceValueRefBase",
    "SequenceValueRefBase",
    "ValueRefBase",
]


class ValueRefBase[T](
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
        T: Type of value at this location

    Example:
        class MyValueRef(ValueRefBase[str], PrimitiveRef, ABC):
            pass
    """

    pass


class SequenceValueRefBase[T](ValueRefBase[T]):
    """Base for primitive values that are children of sequences.

    Same capabilities as ValueRefBase. The distinction is semantic
    and helps with type clarity when building refs for sequence items.

    Type Parameters:
        T: Type of value at this location

    Example:
        class MySequenceItemRef(SequenceValueRefBase[int], PrimitiveRef, ABC):
            pass
    """

    pass


class MutableSequenceValueRefBase[T](SequenceValueRefBase[T]):
    """Mutable variant for sequence item refs.

    Same operations as SequenceValueRefBase since primitive value operations
    (get, set, remove) work through the parent view regardless of mutability.

    Type Parameters:
        T: Type of value at this location
    """

    pass


class MappingValueRefBase[T](ValueRefBase[T]):
    """Base for primitive values that are children of mappings.

    Same capabilities as ValueRefBase. The distinction is semantic
    and helps with type clarity when building refs for mapping values.

    Type Parameters:
        T: Type of value at this location

    Example:
        class MyMappingValueRef(MappingValueRefBase[str], PrimitiveRef, ABC):
            pass
    """

    pass


class MutableMappingValueRefBase[T](MappingValueRefBase[T]):
    """Mutable variant for mapping value refs.

    Same operations as MappingValueRefBase since primitive value operations
    (get, set, remove) work through the parent view regardless of mutability.

    Type Parameters:
        T: Type of value at this location
    """

    pass
