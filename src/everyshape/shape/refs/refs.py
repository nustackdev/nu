"""Complete reference implementations.

This module provides ready-to-use ref classes that combine:
- Base classes from base.py (PrimitiveRefBase, ViewRefBase)
- Capability implementation mixins from bases.py

These are the actual ref classes users will work with or extend.
Each implements the corresponding protocol from collections.py.

Implementation Hierarchy:
    PrimitiveRef combines:
        ExistableBase + GettableBase + SettableBase + DeletableBase + PrimitiveObservableBase

    SequenceRefImpl combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase +
        ViewObservableBase + SequenceIndexableBase + SequenceIterableBase

    MutableSequenceRefImpl adds:
        AppendableBase + InsertableBase + PoppableBase

    MappingRefImpl combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase +
        ViewObservableBase + MappingNestableBase + KeysQueryableBase + ValuesQueryableBase +
        ItemsQueryableBase + MappingIterableBase

    SetRefImpl combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase +
        ViewObservableBase

    MutableSetRefImpl adds:
        SetAddableBase + SetRemovableBase

Usage:
    # Use directly
    class MyListRef(MutableSequenceRefImpl[int, ItemRef, SliceRef]):
        ...

    # Or extend with custom behavior
    class SpecialListRef(SequenceRefImpl[str, StrRef, SliceRef]):
        def custom_method(self): ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping as PyMapping
from collections.abc import Sequence as PySequence
from collections.abc import Set as PySet

from everyshape.types import Value

from ..term import PrimitiveRef, RValue, ViewRef
from ..values import DictValue, ListValue, SetValue
from .bases import (
    AppendableBase,
    ClearableBase,
    DeletableBase,
    # Core capability bases
    ExistableBase,
    ExtractableBase,
    GettableBase,
    InsertableBase,
    ItemsQueryableBase,
    # Query bases
    KeysQueryableBase,
    LengthableBase,
    MappingIterableBase,
    # Mapping capability bases
    MappingNestableBase,
    PoppableBase,
    # Observable bases
    PrimitiveObservableBase,
    # Sequence capability bases
    SequenceIndexableBase,
    SequenceIterableBase,
    # Set capability bases
    SetAddableBase,
    SetRemovableBase,
    SettableBase,
    StorableBase,
    ValuesQueryableBase,
    ViewObservableBase,
)


__all__ = [  # noqa: RUF022
    # Primitive ref implementation
    "PrimitiveRefImpl",
    # Sequence ref implementations
    "SequenceRefImpl",
    "MutableSequenceRefImpl",
    # Mapping ref implementations
    "MappingRefImpl",
    "MutableMappingRefImpl",
    # Set ref implementations
    "SetRefImpl",
    "MutableSetRefImpl",
]


# =============================================================================
# PRIMITIVE REF IMPLEMENTATION
# =============================================================================


class PrimitiveRefImpl[T: Value](
    ExistableBase,
    GettableBase[T],
    SettableBase[T],
    DeletableBase,
    PrimitiveObservableBase,
    PrimitiveRef[T],
):
    """Complete implementation for primitive (leaf) value references.

    Combines all capability bases needed for a full-featured primitive ref:
    - exists(), missing() from ExistableBase
    - get() from GettableBase
    - set() from SettableBase
    - remove() from DeletableBase
    - on_change() from PrimitiveObservableBase

    Implements PrimitiveRefProtocol from collections.py.

    Type Parameters:
        T: Type of value at this location

    Example:
        class NameRef(PrimitiveRefImpl[str]):
            def __init__(self, parent: ViewRef, address: str):
                self._parent = parent
                self._address = address
                self.value_type = str

            @property
            def parent(self) -> ViewRef:
                return self._parent

            def resolve(self, context):
                return self._parent.resolve(context) / self._address
    """

    pass


# =============================================================================
# SEQUENCE REF IMPLEMENTATIONS
# =============================================================================


class SequenceRefImpl[T: Value, ItemRefT, SliceRefT](
    ExistableBase,
    ExtractableBase[ListValue[T], PySequence[T]],
    StorableBase[ListValue[T], PySequence[T]],
    ClearableBase,
    LengthableBase,
    ViewObservableBase,
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
        class ListRef(SequenceRefImpl[int, ItemRef, SliceRef]):
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


class MutableSequenceRefImpl[T: Value, ItemRefT, SliceRefT](
    SequenceRefImpl[T, ItemRefT, SliceRefT],
    AppendableBase[T],
    InsertableBase[T],
    PoppableBase[T],
    ABC,
):
    """Complete implementation for mutable sequence references.

    Extends SequenceRefImpl with mutation capabilities:
    - append() from AppendableBase
    - insert() from InsertableBase
    - pop() from PoppableBase

    Implements MutableSequenceRefProtocol from collections.py.

    Type Parameters:
        T: Type of items in the sequence
        ItemRefT: Type of reference returned for single items
        SliceRefT: Type of reference returned for slices

    Example:
        class MutableListRef(MutableSequenceRefImpl[str, ItemRef, SliceRef]):
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


class MappingRefImpl[K, V: Value, ChildRefT](
    ExistableBase,
    ExtractableBase[DictValue[K, V], PyMapping[K, V]],
    StorableBase[DictValue[K, V], PyMapping[K, V]],
    ClearableBase,
    LengthableBase,
    ViewObservableBase,
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
        class DictRef(MappingRefImpl[str, int, ValueRef]):
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


class MutableMappingRefImpl[K, V: Value, ChildRefT](
    MappingRefImpl[K, V, ChildRefT],
    ABC,
):
    """Complete implementation for mutable mapping references.

    Same capabilities as MappingRefImpl - mutations happen through child refs.

    Implements MutableMappingRefProtocol from collections.py.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ChildRefT: Type of reference returned for child items

    Example:
        class MutableDictRef(MutableMappingRefImpl[str, int, ValueRef]):
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


class SetRefImpl[T: Value](
    ExistableBase,
    ExtractableBase[SetValue[T], PySet[T]],
    StorableBase[SetValue[T], PySet[T]],
    ClearableBase,
    LengthableBase,
    ViewObservableBase,
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
        class TagsRef(SetRefImpl[str]):
            item_type = str

            def result(self, op):
                return SetValue(op)
    """

    item_type: type[T]

    @abstractmethod
    def result(self, op: RValue) -> SetValue[T]:
        """Convert operation result to SetValue wrapper."""
        ...


class MutableSetRefImpl[T: Value](
    SetRefImpl[T],
    SetAddableBase[T],
    SetRemovableBase[T],
    ABC,
):
    """Complete implementation for mutable set references.

    Extends SetRefImpl with mutation capabilities:
    - add() from SetAddableBase
    - remove(), discard() from SetRemovableBase

    Implements MutableSetRefProtocol from collections.py.

    Type Parameters:
        T: Type of items in the set

    Example:
        class MutableTagsRef(MutableSetRefImpl[str]):
            item_type = str

            def result(self, op):
                return SetValue(op)
    """

    pass
