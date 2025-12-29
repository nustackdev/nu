"""Complete reference implementations.

This module provides ready-to-use ref classes that combine:
- Base classes from base.py (PrimitiveRefBase, ViewRefBase)
- Capability implementation mixins from bases.py

These are the actual ref classes users will work with or extend.
Each implements the corresponding protocol from collections.py.

Implementation Hierarchy:
    PrimitiveRef combines:
        ExistableBase + GettableBase + SettableBase + DeletableBase + PrimitiveObservableBase

    SequenceRef combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase +
        ViewObservableBase + SequenceIndexableBase + SequenceIterableBase

    MutableSequenceRef adds:
        AppendableBase + InsertableBase + PoppableBase

    MappingRef combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase +
        ViewObservableBase + MappingNestableBase + KeysQueryableBase + ValuesQueryableBase +
        ItemsQueryableBase + MappingIterableBase

    SetRef combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase +
        ViewObservableBase

    MutableSetRef adds:
        SetAddableBase + SetRemovableBase

Usage:
    # Use directly
    class MyListRef(MutableSequenceRef[int, ItemRef, SliceRef]):
        ...

    # Or extend with custom behavior
    class SpecialListRef(SequenceRef[str, StrRef, SliceRef]):
        def custom_method(self): ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping as PyMapping
from collections.abc import Sequence as PySequence
from collections.abc import Set as PySet

from ..term import RValue, ViewRef
from ..values import DictValue, ListValue, SetValue
from .bases import (
    AppendableBase,
    ClearableBase,
    ExistableBase,
    ExtractableBase,
    InsertableBase,
    ItemsQueryableBase,
    KeysQueryableBase,
    LengthableBase,
    MappingIterableBase,
    MappingNestableBase,
    PoppableBase,
    SequenceIndexableBase,
    SequenceIterableBase,
    SetAddableBase,
    SetRemovableBase,
    StorableBase,
    ValuesQueryableBase,
    ViewObservableBase,
)


__all__ = [
    "MappingRef",
    "MutableMappingRef",
    "MutableSequenceRef",
    "MutableSetRef",
    "SequenceRef",
    "SetRef",
]

# =============================================================================
# SEQUENCE REF IMPLEMENTATIONS
# =============================================================================


class SequenceRef[T, ItemRefT, SliceRefT](
    ExistableBase,
    ExtractableBase[ListValue[T]],
    StorableBase[ListValue[T], PySequence[T]],
    ClearableBase,
    LengthableBase,
    SequenceIndexableBase[T, ItemRefT, SliceRefT],
    SequenceIterableBase[T],
    ViewRef,
    ABC,
):
    """Complete implementation for read-only sequence references.

    Combines all capability bases needed for a full-featured sequence ref:
    - exists(), missing() from ExistableBase
    - extract() from ExtractableBase
    - store() from StorableBase
    - clear() from ClearableBase
    - length() from LengthableBase
    - on_change(), on_child_change(), etc. from ViewObservableBase
    - __getitem__ from SequenceIndexableBase
    - map(), filter(), reduce(), find(), etc. from SequenceIterableBase

    Implements SequenceRefProtocol from collections.py.

    Type Parameters:
        T: Type of items in the sequence
        ItemRefT: Type of reference returned for single items
        SliceRefT: Type of reference returned for slices

    Subclasses must implement:
        - _create_item_ref(index) -> ItemRefT
        - _create_slice_ref(slice) -> SliceRefT
        - result(op) -> ListValue[T]
        - item_type property

    Example:
        class ListRef(SequenceRef[int, ItemRef, SliceRef]):
            item_type = int

            def _create_item_ref(self, index):
                return ItemRef(self, index)

            def _create_slice_ref(self, key):
                return SliceRef(self, key)

            def result(self, op):
                return ListValue(op)
    """

    item_type: type[T]

    @abstractmethod
    def result(self, op: RValue) -> ListValue[T]:
        """Convert operation result to ListValue wrapper."""
        ...


class MutableSequenceRef[T, ItemRefT, SliceRefT](
    SequenceRef[T, ItemRefT, SliceRefT],
    AppendableBase[T],
    InsertableBase[T],
    PoppableBase[T],
    ViewObservableBase,
    ABC,
):
    """Complete implementation for mutable sequence references.

    Extends SequenceRef with mutation capabilities:
    - append() from AppendableBase
    - insert() from InsertableBase
    - pop() from PoppableBase

    Implements MutableSequenceRefProtocol from collections.py.

    Type Parameters:
        T: Type of items in the sequence
        ItemRefT: Type of reference returned for single items
        SliceRefT: Type of reference returned for slices

    Example:
        class MutableListRef(MutableSequenceRef[str, ItemRef, SliceRef]):
            item_type = str

            def _create_item_ref(self, index):
                return ItemRef(self, index)

            def _create_slice_ref(self, key):
                return SliceRef(self, key)

            def result(self, op):
                return ListValue(op)
    """

    pass


# =============================================================================
# MAPPING REF IMPLEMENTATIONS
# =============================================================================


class MappingRef[K, V, ChildRefT](
    ExistableBase,
    ExtractableBase[DictValue[K, V]],
    StorableBase[DictValue[K, V], PyMapping[K, V]],
    ClearableBase,
    LengthableBase,
    MappingNestableBase[K, ChildRefT],
    KeysQueryableBase[K],
    ValuesQueryableBase[V],
    ItemsQueryableBase[K, V],
    MappingIterableBase[K, V],
    ViewRef,
    ABC,
):
    """Complete implementation for read-only mapping references.

    Combines all capability bases needed for a full-featured mapping ref:
    - exists(), missing() from ExistableBase
    - extract() from ExtractableBase
    - store() from StorableBase
    - clear() from ClearableBase
    - length() from LengthableBase
    - on_change(), on_child_change(), etc. from ViewObservableBase
    - __getitem__ from MappingNestableBase
    - keys() from KeysQueryableBase
    - values() from ValuesQueryableBase
    - items() from ItemsQueryableBase
    - map_values(), filter(), reduce(), find_key(), etc. from MappingIterableBase

    Implements MappingRefProtocol from collections.py.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ChildRefT: Type of reference returned for child items

    Subclasses must implement:
        - _create_child_ref(key) -> ChildRefT
        - result(op) -> DictValue[K, V]
        - key_type property
        - value_type property

    Example:
        class DictRef(MappingRef[str, int, ValueRef]):
            key_type = str
            value_type = int

            def _create_child_ref(self, key):
                return ValueRef(self, key)

            def result(self, op):
                return DictValue(op)
    """

    key_type: type[K]
    value_type: type[V]

    @abstractmethod
    def result(self, op: RValue) -> DictValue[K, V]:
        """Convert operation result to DictValue wrapper."""
        ...


class MutableMappingRef[K, V, ChildRefT](
    MappingRef[K, V, ChildRefT],
    ViewObservableBase,
    ABC,
):
    """Complete implementation for mutable mapping references.

    Same capabilities as MappingRef - mutations happen through child refs.

    Implements MutableMappingRefProtocol from collections.py.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ChildRefT: Type of reference returned for child items

    Example:
        class MutableDictRef(MutableMappingRef[str, int, ValueRef]):
            key_type = str
            value_type = int

            def _create_child_ref(self, key):
                return MutableValueRef(self, key)

            def result(self, op):
                return DictValue(op)
    """

    pass


# =============================================================================
# SET REF IMPLEMENTATIONS
# =============================================================================


class SetRef[T](
    ExistableBase,
    ExtractableBase[SetValue[T]],
    StorableBase[SetValue[T], PySet[T]],
    ClearableBase,
    LengthableBase,
    ViewRef,
    ABC,
):
    """Complete implementation for read-only set references.

    Combines all capability bases needed for a full-featured set ref:
    - exists(), missing() from ExistableBase
    - extract() from ExtractableBase
    - store() from StorableBase
    - clear() from ClearableBase
    - length() from LengthableBase
    - on_change(), on_child_change(), etc. from ViewObservableBase

    Implements SetRefProtocol from collections.py.

    Type Parameters:
        T: Type of items in the set

    Subclasses must implement:
        - result(op) -> SetValue[T]
        - item_type property

    Example:
        class TagsRef(SetRef[str]):
            item_type = str

            def result(self, op):
                return SetValue(op)
    """

    item_type: type[T]

    @abstractmethod
    def result(self, op: RValue) -> SetValue[T]:
        """Convert operation result to SetValue wrapper."""
        ...


class MutableSetRef[T](
    SetRef[T],
    SetAddableBase[T],
    SetRemovableBase[T],
    ViewObservableBase,
    ABC,
):
    """Complete implementation for mutable set references.

    Extends SetRef with mutation capabilities:
    - add() from SetAddableBase
    - remove(), discard() from SetRemovableBase

    Implements MutableSetRefProtocol from collections.py.

    Type Parameters:
        T: Type of items in the set

    Example:
        class MutableTagsRef(MutableSetRef[str]):
            item_type = str

            def result(self, op):
                return SetValue(op)
    """

    pass
