"""Complete reference base implementations.

This module provides ready-to-extend ref base classes that combine capability implementation mixins from bases.py

These are the abstract base classes users will extend in everybase
to create final types like ListRef, DictRef, SetRef, etc.

Implementation Hierarchy:
    SequenceRefBase combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase +
        SequenceIndexableBase + SequenceIterableBase + ViewRef

    MutableSequenceRefBase extends SequenceRefBase:
        + AppendableBase + InsertableBase + PoppableBase + ViewObservableBase

    MappingRefBase combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase +
        MappingNestableBase + KeysQueryableBase + ValuesQueryableBase +
        ItemsQueryableBase + MappingIterableBase + ViewRef

    MutableMappingRefBase extends MappingRefBase:
        + ViewObservableBase

    SetRefBase combines:
        ExistableBase + ExtractableBase + StorableBase + ClearableBase + LengthableBase + ViewRef

    MutableSetRefBase extends SetRefBase:
        + SetAddableBase + SetRemovableBase + ViewObservableBase

Usage in everybase:
    class ListRef(MutableSequenceRefBase[int, ItemRef, SliceRef]):
        item_type = int

        def _create_item_ref(self, index):
            return ItemRef(self, index)

        def _create_slice_ref(self, key):
            return SliceRef(self, key)

        def result(self, op):
            return ListValue(op)
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
    "MappingRefBase",
    "MutableMappingRefBase",
    "MutableSequenceRefBase",
    "MutableSetRefBase",
    "SequenceRefBase",
    "SetRefBase",
]

# =============================================================================
# SEQUENCE REF BASE IMPLEMENTATIONS
# =============================================================================


class SequenceRefBase[T, ItemRefT, SliceRefT](
    ExistableBase,
    ExtractableBase[ListValue[T]],
    StorableBase[ListValue[T], PySequence[T]],
    ClearableBase,
    LengthableBase,
    SequenceIndexableBase[T, ItemRefT, SliceRefT],
    SequenceIterableBase[T],
    ABC,
):
    """Base class for read-only sequence references.

    Combines all capability bases needed for a full-featured sequence ref:
    - exists(), missing() from ExistableBase
    - extract() from ExtractableBase
    - store() from StorableBase
    - clear() from ClearableBase
    - length() from LengthableBase
    - __getitem__ from SequenceIndexableBase
    - map(), filter(), reduce(), find(), etc. from SequenceIterableBase

    Implements SequenceRef protocol from collections.py.

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
        class ListRef(SequenceRefBase[int, ItemRef, SliceRef]):
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
        """Wrap an operation result in a ListValue container.

        Args:
            op: The operation to wrap

        Returns:
            ListValue wrapping the operation
        """
        ...


class MutableSequenceRefBase[T, ItemRefT, SliceRefT](
    SequenceRefBase[T, ItemRefT, SliceRefT],
    AppendableBase[T],
    InsertableBase[T],
    PoppableBase[T],
    ViewObservableBase,
    ABC,
):
    """Base class for mutable sequence references.

    Extends SequenceRefBase with mutation and observation capabilities:
    - append() from AppendableBase
    - insert() from InsertableBase
    - pop() from PoppableBase
    - on_change(), on_child_change(), etc. from ViewObservableBase

    Implements MutableSequenceRef protocol from collections.py.

    Type Parameters:
        T: Type of items in the sequence
        ItemRefT: Type of reference returned for single items
        SliceRefT: Type of reference returned for slices

    Example:
        class MutableListRef(MutableSequenceRefBase[str, ItemRef, SliceRef]):
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
# MAPPING REF BASE IMPLEMENTATIONS
# =============================================================================


class MappingRefBase[K, V, ChildRefT](
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
    """Base class for read-only mapping references.

    Combines all capability bases needed for a full-featured mapping ref:
    - exists(), missing() from ExistableBase
    - extract() from ExtractableBase
    - store() from StorableBase
    - clear() from ClearableBase
    - length() from LengthableBase
    - __getitem__ from MappingNestableBase
    - keys() from KeysQueryableBase
    - values() from ValuesQueryableBase
    - items() from ItemsQueryableBase
    - map_values(), filter(), reduce(), find_key(), etc. from MappingIterableBase

    Implements MappingRef protocol from collections.py.

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
        class DictRef(MappingRefBase[str, int, ValueRef]):
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
        """Wrap an operation result in a DictValue container.

        Args:
            op: The operation to wrap

        Returns:
            DictValue wrapping the operation
        """
        ...


class MutableMappingRefBase[K, V, ChildRefT](
    MappingRefBase[K, V, ChildRefT],
    ViewObservableBase,
    ABC,
):
    """Base class for mutable mapping references.

    Extends MappingRefBase with observation capabilities.
    Mutations happen through child refs obtained via __getitem__.

    Implements MutableMappingRef protocol from collections.py.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ChildRefT: Type of reference returned for child items

    Example:
        class MutableDictRef(MutableMappingRefBase[str, int, ValueRef]):
            key_type = str
            value_type = int

            def _create_child_ref(self, key):
                return MutableValueRef(self, key)

            def result(self, op):
                return DictValue(op)
    """

    pass


# =============================================================================
# SET REF BASE IMPLEMENTATIONS
# =============================================================================


class SetRefBase[T](
    ExistableBase,
    ExtractableBase[SetValue[T]],
    StorableBase[SetValue[T], PySet[T]],
    ClearableBase,
    LengthableBase,
    ViewRef,
    ABC,
):
    """Base class for read-only set references.

    Combines all capability bases needed for a full-featured set ref:
    - exists(), missing() from ExistableBase
    - extract() from ExtractableBase
    - store() from StorableBase
    - clear() from ClearableBase
    - length() from LengthableBase

    Implements SetRef protocol from collections.py.

    Type Parameters:
        T: Type of items in the set

    Subclasses must implement:
        - result(op) -> SetValue[T]
        - item_type property

    Example:
        class TagsRef(SetRefBase[str]):
            item_type = str

            def result(self, op):
                return SetValue(op)
    """

    item_type: type[T]

    @abstractmethod
    def result(self, op: RValue) -> SetValue[T]:
        """Wrap an operation result in a SetValue container.

        Args:
            op: The operation to wrap

        Returns:
            SetValue wrapping the operation
        """
        ...


class MutableSetRefBase[T](
    SetRefBase[T],
    SetAddableBase[T],
    SetRemovableBase[T],
    ViewObservableBase,
    ABC,
):
    """Base class for mutable set references.

    Extends SetRefBase with mutation and observation capabilities:
    - add() from SetAddableBase
    - remove(), discard() from SetRemovableBase
    - on_change(), on_child_change(), etc. from ViewObservableBase

    Implements MutableSetRef protocol from collections.py.

    Type Parameters:
        T: Type of items in the set

    Example:
        class MutableTagsRef(MutableSetRefBase[str]):
            item_type = str

            def result(self, op):
                return SetValue(op)
    """

    pass
