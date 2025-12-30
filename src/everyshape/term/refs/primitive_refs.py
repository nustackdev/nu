"""Primitive value reference implementations.

This module provides ready-to-use ref classes for primitive (leaf) values
that combine base classes and capability implementation mixins.

These refs point to leaf nodes in the tree (int, str, float, bool, etc.)
and support read, write, delete, and observation operations.

Implementation Hierarchy:
    ValueRef combines:
        ExistableBase + GettableBase + SettableBase + DeletableBase + PrimitiveObservableBase

    SequenceValueRef extends ValueRef:
        For primitive values that are children of sequences (list items)

    MappingValueRef extends ValueRef:
        For primitive values that are children of mappings (dict values)

    MutableSequenceValueRef extends SequenceValueRef:
        Mutable variant for sequence children (same ops, different context)

    MutableMappingValueRef extends MappingValueRef:
        Mutable variant for mapping children (same ops, different context)

Usage:
    class MyShape(Shape):
        name: ValueRef[str] = ValueSlot(str)
        age: ValueRef[int] = ValueSlot(int)

    # Create operations
    MyShape.name.get()          # GetOp[str] -> StrValue
    MyShape.name.set("Alice")   # SetCmd[str] -> StrValue
    MyShape.name.remove()       # DeleteCmd -> NoneValue
    MyShape.name.exists()       # ExistsOp -> BoolValue
    MyShape.name.on_change()    # OnPrimitiveChangeOp -> Subscription
"""

from __future__ import annotations

from abc import ABC

from ..term import PrimitiveRef
from .bases import (
    DeletableBase,
    ExistableBase,
    GettableBase,
    PrimitiveObservableBase,
    SettableBase,
)


__all__ = [
    "MappingValueRef",
    "MutableMappingValueRef",
    "MutableSequenceValueRef",
    "SequenceValueRef",
    "ValueRef",
]


# =============================================================================
# BASE VALUE REF
# =============================================================================


class ValueRef[T](  # type: ignore[misc]  # PrimitiveRef.value_type is set at __init__, bases declare it generically
    ExistableBase,
    GettableBase[T],
    SettableBase[T],
    DeletableBase,
    PrimitiveObservableBase,
    PrimitiveRef,
    ABC,
):
    """Complete implementation for primitive value references.

    Combines all capability bases needed for a full-featured primitive ref:
    - exists(), missing() from ExistableBase
    - get() from GettableBase
    - set() from SettableBase
    - remove() from DeletableBase
    - on_change() from PrimitiveObservableBase

    Implements ValueRefProtocol from collections.py.

    Type Parameters:
        T: Type of value at this location (int, str, float, bool, etc.)

    Subclasses must have:
        - value_type: type[T] attribute (inherited from PrimitiveRef)

    Example:
        class NameRef(ValueRef[str]):
            value_type = str

        # Usage
        name_ref = shape.name
        get_op = name_ref.get()      # Returns StrValue
        set_cmd = name_ref.set("x")  # Returns StrValue
        del_cmd = name_ref.remove()  # Returns NoneValue
        exists = name_ref.exists()   # Returns BoolValue
        sub_op = name_ref.on_change() # Returns OnPrimitiveChangeOp
    """

    pass


# =============================================================================
# SEQUENCE VALUE REF
# =============================================================================


class SequenceValueRef[T](ValueRef[T], ABC):
    """Reference to a primitive value that is a child of a sequence.

    Used for individual items in a list-like container where items are
    primitive values (not nested structures).

    Same capabilities as ValueRef - the distinction is semantic and
    helps with type clarity when building refs for sequence items.

    Type Parameters:
        T: Type of value at this location

    Example:
        # A list of integers
        class NumbersListRef(SequenceRef[int, SequenceValueRef[int], SliceRef]):
            item_type = int

            def _create_item_ref(self, index):
                return SequenceValueRef[int](
                    address=index,
                    value_type=int,
                    parent_ref=self,
                )

        # Usage
        numbers = shape.numbers  # SequenceRef
        first = numbers[0]       # SequenceValueRef[int]
        first.get()              # GetOp -> IntValue
        first.set(42)            # SetCmd -> IntValue
    """

    pass


class MutableSequenceValueRef[T](SequenceValueRef[T], ABC):
    """Mutable variant of SequenceValueRef.

    Same operations as SequenceValueRef since primitive value operations
    (get, set, remove) work through the parent view regardless of mutability.

    The mutability distinction is at the parent sequence level, not the
    individual value level. This class exists for type system clarity.

    Type Parameters:
        T: Type of value at this location

    Example:
        class MutableNumbersRef(MutableSequenceRef[int, MutableSequenceValueRef[int], SliceRef]):
            item_type = int

            def _create_item_ref(self, index):
                return MutableSequenceValueRef[int](...)
    """

    pass


# =============================================================================
# MAPPING VALUE REF
# =============================================================================


class MappingValueRef[T](ValueRef[T], ABC):
    """Reference to a primitive value that is a child of a mapping.

    Used for values in a dict-like container where values are primitive
    values (not nested structures).

    Same capabilities as ValueRef - the distinction is semantic and
    helps with type clarity when building refs for mapping values.

    Type Parameters:
        T: Type of value at this location

    Example:
        # A dict of string -> int
        class ScoresRef(MappingRef[str, int, MappingValueRef[int]]):
            key_type = str
            value_type = int

            def _create_child_ref(self, key):
                return MappingValueRef[int](
                    address=key,
                    value_type=int,
                    parent_ref=self,
                )

        # Usage
        scores = shape.scores     # MappingRef
        alice = scores["alice"]   # MappingValueRef[int]
        alice.get()               # GetOp -> IntValue
        alice.set(100)            # SetCmd -> IntValue
    """

    pass


class MutableMappingValueRef[T](MappingValueRef[T], ABC):
    """Mutable variant of MappingValueRef.

    Same operations as MappingValueRef since primitive value operations
    (get, set, remove) work through the parent view regardless of mutability.

    The mutability distinction is at the parent mapping level, not the
    individual value level. This class exists for type system clarity.

    Type Parameters:
        T: Type of value at this location

    Example:
        class MutableScoresRef(MutableMappingRef[str, int, MutableMappingValueRef[int]]):
            key_type = str
            value_type = int

            def _create_child_ref(self, key):
                return MutableMappingValueRef[int](...)
    """

    pass
