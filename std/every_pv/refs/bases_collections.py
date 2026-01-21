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

Type Parameters (matching protocol conventions):
    CollectionT: Native Python collection type (list, dict, set)
    ItemT: Native Python item type for sequences/sets (int, str, nested dict, etc.)
    KeyT: Native Python key type for mappings (str, int, etc.)
    ValueT: Native Python value type for mappings (int, nested dict, etc.)
    CollectionValueT: ComputedValue type for collection (ListType, DictType, SetType)
    ItemValueT: ComputedValue type for items (IntType, StrType, AnyType, etc.)
    KeyValueT: ComputedValue type for keys (StrType, IntType, etc.)
    ValueValueT: ComputedValue type for values (IntType, AnyType, etc.)
    ViewT: View type at this location
    IndexT: Index type for sequences (commonly int)
    IndexValueT: ComputedValue type for index (commonly IntType)
    SliceValueT: ComputedValue type for sliced results
    ItemRefT: Reference type for individual items
    SliceRefT: Reference type for slices
    ChildRefT: Reference type for child items in mappings

Usage in everybase:
    class ListRef(MutableSequenceRefBase[
        list[int],           # CollectionT
        int,                 # ItemT
        ListType[int],      # CollectionValueT
        IntType,            # ItemValueT
        ListView,            # ViewT
        int,                 # IndexT
        IntType,            # IndexValueT
        ListType[int],      # SliceValueT
        ItemRef,             # ItemRefT
        SliceRef,            # SliceRefT
    ]):
        collection_type = list
        item_type = int
        collection_value_type = ListType
        item_value_type = IntType

        def _create_item_ref(self, index):
            return ItemRef(self, index)

        def _create_slice_ref(self, key):
            return SliceRef(self, key)

        def result(self, op):
            return ListType(op)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from every._abc import Term

from .bases import (
    AppendableBase,
    ClearableBase,
    ExistableBase,
    ExtractableBase,
    InsertableBase,
    ItemsQueryableBase,
    KeysQueryableBase,
    LengthableBase,
    MappingAccessibleBase,
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
from .ref import ViewRef


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


class SequenceRefBase[
    CollectionT,
    ItemT,
    CollectionValueT,
    ItemValueT,
    ViewT,
    IndexT,
    IndexValueT,
    SliceValueT,
    ItemRefT,
    SliceRefT,
](
    ExistableBase,
    ExtractableBase[CollectionValueT],
    StorableBase[CollectionValueT, CollectionT],
    ClearableBase,
    LengthableBase,
    SequenceIndexableBase[ItemT, ItemRefT, SliceRefT],
    SequenceIterableBase[ItemT],
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
        CollectionT: Native Python collection type (list, tuple, etc.)
        ItemT: Native Python item type (int, str, nested dict, etc.)
        CollectionValueT: ComputedValue type for collection (ListType, TupleType, etc.)
        ItemValueT: ComputedValue type for items (IntType, StrType, AnyType, etc.)
        ViewT: View type at this location
        IndexT: Index type (commonly int)
        IndexValueT: ComputedValue type for index (commonly IntType)
        SliceValueT: ComputedValue type for sliced results
        ItemRefT: Reference type for individual items
        SliceRefT: Reference type for slices

    Subclasses must implement:
        - _create_item_ref(index) -> ItemRefT
        - _create_slice_ref(slice) -> SliceRefT
        - result(op) -> CollectionValueT
        - collection_type property
        - item_type property
        - collection_value_type property
        - item_value_type property

    Example:
        class ListRef(SequenceRefBase[
            list[int], int, ListType[int], IntType,
            ListView, int, IntType, ListType[int],
            ItemRef, SliceRef
        ]):
            collection_type = list
            item_type = int
            collection_value_type = ListType
            item_value_type = IntType

            def _create_item_ref(self, index):
                return ItemRef(self, index)

            def _create_slice_ref(self, key):
                return SliceRef(self, key)

            def result(self, op):
                return ListType(op)
    """

    collection_type: type[CollectionT]
    item_type: type[ItemT]
    collection_value_type: type[CollectionValueT]
    item_value_type: type[ItemValueT]
    view_type: type[ViewT]
    index_type: type[IndexT]
    index_value_type: type[IndexValueT]

    @abstractmethod
    def result(self, op: Term) -> CollectionValueT:
        """Wrap an operation result in the appropriate collection value container.

        Args:
            op: The operation to wrap

        Returns:
            CollectionValueT wrapping the operation (e.g., ListType)
        """
        ...


class MutableSequenceRefBase[
    CollectionT,
    ItemT,
    CollectionValueT,
    ItemValueT,
    ViewT,
    IndexT,
    IndexValueT,
    SliceValueT,
    ItemRefT,
    SliceRefT,
](
    SequenceRefBase[
        CollectionT,
        ItemT,
        CollectionValueT,
        ItemValueT,
        ViewT,
        IndexT,
        IndexValueT,
        SliceValueT,
        ItemRefT,
        SliceRefT,
    ],
    AppendableBase[ItemT],
    InsertableBase[ItemT],
    PoppableBase[ItemT],
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
        CollectionT: Native Python collection type (list, tuple, etc.)
        ItemT: Native Python item type (int, str, nested dict, etc.)
        CollectionValueT: ComputedValue type for collection (ListType, TupleType, etc.)
        ItemValueT: ComputedValue type for items (IntType, StrType, AnyType, etc.)
        ViewT: View type at this location
        IndexT: Index type (commonly int)
        IndexValueT: ComputedValue type for index (commonly IntType)
        SliceValueT: ComputedValue type for sliced results
        ItemRefT: Reference type for individual items
        SliceRefT: Reference type for slices

    Example:
        class MutableListRef(MutableSequenceRefBase[
            list[str], str, ListType[str], StrType,
            ListView, int, IntType, ListType[str],
            ItemRef, SliceRef
        ]):
            collection_type = list
            item_type = str
            collection_value_type = ListType
            item_value_type = StrType

            def _create_item_ref(self, index):
                return ItemRef(self, index)

            def _create_slice_ref(self, key):
                return SliceRef(self, key)

            def result(self, op):
                return ListType(op)
    """

    pass


# =============================================================================
# MAPPING REF BASE IMPLEMENTATIONS
# =============================================================================


class MappingRefBase[
    CollectionT,
    KeyT,
    ValueT,
    CollectionValueT,
    KeyValueT,
    ValueValueT,
    ViewT,
    ChildRefT,
](
    ExistableBase,
    ExtractableBase[CollectionValueT],
    StorableBase[CollectionValueT, CollectionT],
    ClearableBase,
    LengthableBase,
    MappingNestableBase[KeyT, ChildRefT],
    KeysQueryableBase[KeyT],
    ValuesQueryableBase[ValueT],
    ItemsQueryableBase[KeyT, ValueT],
    MappingIterableBase[KeyT, ValueT],
    MappingAccessibleBase[KeyT, ValueT],
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
    - get(), set_item(), remove_item() from MappingAccessibleBase

    Implements MappingRef protocol from collections.py.

    Type Parameters:
        CollectionT: Native Python collection type (dict, etc.)
        KeyT: Native Python key type (str, int, etc.)
        ValueT: Native Python value type (int, nested dict, etc.)
        CollectionValueT: ComputedValue type for collection (DictType, etc.)
        KeyValueT: ComputedValue type for keys (StrType, IntType, etc.)
        ValueValueT: ComputedValue type for values (IntType, AnyType, etc.)
        ViewT: View type at this location
        ChildRefT: Reference type for child items

    Subclasses must implement:
        - _create_child_ref(key) -> ChildRefT
        - result(op) -> CollectionValueT
        - collection_type property
        - key_type property
        - value_type property
        - collection_value_type property
        - key_value_type property
        - value_value_type property

    Example:
        class DictRef(MappingRefBase[
            dict[str, int], str, int, DictType[str, int],
            StrType, IntType, DictView, ValueRef
        ]):
            collection_type = dict
            key_type = str
            value_type = int
            collection_value_type = DictType
            key_value_type = StrType
            value_value_type = IntType

            def _create_child_ref(self, key):
                return ValueRef(self, key)

            def result(self, op):
                return DictType(op)
    """

    collection_type: type[CollectionT]
    key_type: type[KeyT]
    value_type: type[ValueT]
    collection_value_type: type[CollectionValueT]
    key_value_type: type[KeyValueT]
    value_value_type: type[ValueValueT]
    view_type: type[ViewT]

    @abstractmethod
    def result(self, op: Term) -> CollectionValueT:
        """Wrap an operation result in the appropriate collection value container.

        Args:
            op: The operation to wrap

        Returns:
            CollectionValueT wrapping the operation (e.g., DictType)
        """
        ...


class MutableMappingRefBase[
    CollectionT,
    KeyT,
    ValueT,
    CollectionValueT,
    KeyValueT,
    ValueValueT,
    ViewT,
    ChildRefT,
](
    MappingRefBase[
        CollectionT,
        KeyT,
        ValueT,
        CollectionValueT,
        KeyValueT,
        ValueValueT,
        ViewT,
        ChildRefT,
    ],
    ViewObservableBase,
    ABC,
):
    """Base class for mutable mapping references.

    Extends MappingRefBase with observation capabilities.
    Mutations happen through child refs obtained via __getitem__.

    Implements MutableMappingRef protocol from collections.py.

    Type Parameters:
        CollectionT: Native Python collection type (dict, etc.)
        KeyT: Native Python key type (str, int, etc.)
        ValueT: Native Python value type (int, nested dict, etc.)
        CollectionValueT: ComputedValue type for collection (DictType, etc.)
        KeyValueT: ComputedValue type for keys (StrType, IntType, etc.)
        ValueValueT: ComputedValue type for values (IntType, AnyType, etc.)
        ViewT: View type at this location
        ChildRefT: Reference type for child items

    Example:
        class MutableDictRef(MutableMappingRefBase[
            dict[str, int], str, int, DictType[str, int],
            StrType, IntType, DictView, MutableValueRef
        ]):
            collection_type = dict
            key_type = str
            value_type = int
            collection_value_type = DictType
            key_value_type = StrType
            value_value_type = IntType

            def _create_child_ref(self, key):
                return MutableValueRef(self, key)

            def result(self, op):
                return DictType(op)
    """

    pass


# =============================================================================
# SET REF BASE IMPLEMENTATIONS
# =============================================================================


class SetRefBase[
    CollectionT,
    ItemT,
    CollectionValueT,
    ItemValueT,
    ViewT,
](
    ExistableBase,
    ExtractableBase[CollectionValueT],
    StorableBase[CollectionValueT, CollectionT],
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
        CollectionT: Native Python collection type (set, frozenset, etc.)
        ItemT: Native Python item type (int, str, etc.)
        CollectionValueT: ComputedValue type for collection (SetType, etc.)
        ItemValueT: ComputedValue type for items (IntType, StrType, etc.)
        ViewT: View type at this location

    Subclasses must implement:
        - result(op) -> CollectionValueT
        - collection_type property
        - item_type property
        - collection_value_type property
        - item_value_type property

    Example:
        class TagsRef(SetRefBase[
            set[str], str, SetType[str], StrType, SetView
        ]):
            collection_type = set
            item_type = str
            collection_value_type = SetType
            item_value_type = StrType

            def result(self, op):
                return SetType(op)
    """

    collection_type: type[CollectionT]
    item_type: type[ItemT]
    collection_value_type: type[CollectionValueT]
    item_value_type: type[ItemValueT]
    view_type: type[ViewT]

    @abstractmethod
    def result(self, op: Term) -> CollectionValueT:
        """Wrap an operation result in the appropriate collection value container.

        Args:
            op: The operation to wrap

        Returns:
            CollectionValueT wrapping the operation (e.g., SetType)
        """
        ...


class MutableSetRefBase[
    CollectionT,
    ItemT,
    CollectionValueT,
    ItemValueT,
    ViewT,
](
    SetRefBase[CollectionT, ItemT, CollectionValueT, ItemValueT, ViewT],
    SetAddableBase[ItemT],
    SetRemovableBase[ItemT],
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
        CollectionT: Native Python collection type (set, etc.)
        ItemT: Native Python item type (int, str, etc.)
        CollectionValueT: ComputedValue type for collection (SetType, etc.)
        ItemValueT: ComputedValue type for items (IntType, StrType, etc.)
        ViewT: View type at this location

    Example:
        class MutableTagsRef(MutableSetRefBase[
            set[str], str, SetType[str], StrType, SetView
        ]):
            collection_type = set
            item_type = str
            collection_value_type = SetType
            item_value_type = StrType

            def result(self, op):
                return SetType(op)
    """

    pass
