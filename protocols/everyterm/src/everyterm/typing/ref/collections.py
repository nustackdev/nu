"""Collection reference protocol hierarchy.

This module defines collection ref protocols composed from atomic capabilities.
Follows Python's collections.abc hierarchy while using EveryShape's capability system.

These are PROTOCOLS (type contracts) that define what refs CAN do.
Implementations live in bases.py, refs.py, and primitive_refs.py.

Protocol Hierarchy:
    Ref (base)
    ├── ContainerRef (existence checking)
    │   └── CollectionRef (sized, extractable, storable)
    │       ├── SequenceRef[T] (indexed access)
    │       │   └── MutableSequenceRef[T]
    │       ├── MappingRef[K,V] (key access)
    │       │   └── MutableMappingRef[K,V]
    │       └── SetRef[T] (containment)
    │           └── MutableSetRef[T]
    └── PrimitiveRef[T] (leaf value references)
        └── ValueRef[T] (typed primitive value)

Similar to view/collections.py which composes view capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .capabilities import (
    Appendable,
    Clearable,
    Deletable,
    Existable,
    Extractable,
    Gettable,
    Insertable,
    ItemsQueryable,
    KeysQueryable,
    Lengthable,
    MappingAccessible,
    Nestable,
    Poppable,
    RefIndexable,
    RefObservable,
    RefSliceable,
    Settable,
    Storable,
    ValuesQueryable,
)


if TYPE_CHECKING:
    from everyterm.types import NilType


__all__ = [  # noqa: RUF022
    # Base protocols
    "ContainerRef",
    "CollectionRef",
    # Sequence protocols
    "SequenceRef",
    "MutableSequenceRef",
    # Mapping protocols
    "MappingRef",
    "MutableMappingRef",
    # Set protocols
    "SetRef",
    "MutableSetRef",
    # item protocol
    "CollectionItemRef",
]


# =============================================================================
# BASE REF PROTOCOLS
# =============================================================================


@runtime_checkable
class ContainerRef[ViewT](
    Existable,
    Protocol,
):
    """Protocol for refs with existence checking.

    Base protocol for all container refs. Supports checking if the ref exists.

    Type Parameters:

    Example:
        >>> if isinstance(ref, ContainerRef):
        ...     if ref.exists().execute(ctx):
        ...         print("Ref exists")
    """

    @property
    def view_type(self) -> type[ViewT]:
        """Get the view type for this container.

        Returns:
            View class
        """
        ...


@runtime_checkable
class CollectionRef[CollectionT, ItemT, CollectionValueT, ItemValueT, ViewT](
    ContainerRef[ViewT],
    Extractable[CollectionValueT],
    Storable[CollectionT, CollectionValueT],
    Clearable,
    Lengthable,
    Protocol,
):
    """Protocol for sized, observable collection refs.

    Foundation protocol for all collection refs (sequences, mappings, sets).
    Supports extraction, storage, clearing, length queries, and observation.

    Type Parameters:
        CollectionT: Type of this collection (dict, list, etc)
        ItemT: Type of this collection's item (int, float, str, nested list, dict, etc)
        CollectionValueT: ComputedValue type for this collection (ListType, DictType, etc)
        ItemValueT: ComputedValue type for this collection's item (IntType, FloatType, AnyType, etc)
        ViewT: Type of the view at this location

    Example:
        >>> if isinstance(ref, CollectionRef):
        ...     data = ref.extract().execute(ctx)
        ...     ref.store(new_data).execute(ctx)
        ...     length = ref.length().execute(ctx)
    """

    @property
    def item_type(self) -> type[ItemT]:
        """Get the item type for this collection.

        Returns:
            Type of items (int, float, nested dict, list etc)
        """
        ...

    @property
    def collection_type(self) -> type[CollectionT]:
        """Get the collection type.

        Returns:
            Type of collection (dict, list, etc)
        """
        ...

    @property
    def item_value_type(self) -> type[ItemValueT]:
        """Get the ComputedValue type for this collection's items.

        Returns:
            Type of items (IntType, FloatType, AnyType, etc)
        """
        ...

    @property
    def collection_value_type(self) -> type[ItemValueT]:
        """Get the ComputedValue type for this collection.

        Returns:
            Type of collection (DictType, ListType, etc)
        """
        ...


# =============================================================================
# SEQUENCE PROTOCOLS
# =============================================================================


@runtime_checkable
class SequenceRef[
    CollectionT,
    ItemT,
    CollectionValueT,
    ItemValueT,
    ViewT,
    IndexT,
    IndexValueT,
    SliceValueT,
](
    CollectionRef[CollectionT, ItemT, CollectionValueT, ItemValueT, ViewT],
    RefIndexable[IndexT, ItemValueT],
    RefSliceable[SliceValueT],
    Protocol,
):
    """Protocol for read-only sequence references.

    Sequence refs point to list-like containers.
    They support index access, slicing, length, and extraction.

    Type Parameters:
        CollectionT: Type of this collection (list, tuple, etc)
        ItemT: Type of this collection's item (int, float, str, nested list, dict, etc)
        CollectionValueT: ComputedValue type for this collection (ListType, TupleType, etc)
        ItemValueT: ComputedValue type for this collection's item (IntType, FloatType, etc)
        ViewT: Type of the view at this location
        IndexT: Type of index (commonly int)
        IndexValueT: ComputedValue type for index (commonly IntType)
        SliceValueT: ComputedValue type for sliced result

    Example:
        >>> if isinstance(ref, SequenceRef):
        ...     first = ref[0].get().execute(ctx)
        ...     slice_ref = ref[1:5]
        ...     all_items = ref.extract().execute(ctx)
    """

    @property
    def index_type(self) -> type[IndexT]:
        """Get the index type for this sequence.

        Returns:
            Type of index (commonly int)
        """
        ...

    @property
    def index_value_type(self) -> type[IndexValueT]:
        """Get the computed value type for index of this sequence.

        Returns:
            Type of computed value for index (commonly IntType)
        """
        ...


@runtime_checkable
class MutableSequenceRef[
    CollectionT,
    ItemT,
    CollectionValueT,
    ItemValueT,
    ViewT,
    IndexT,
    IndexValueT,
    SliceValueT,
](
    SequenceRef[
        CollectionT,
        ItemT,
        CollectionValueT,
        ItemValueT,
        ViewT,
        IndexT,
        IndexValueT,
        SliceValueT,
    ],
    Appendable[ItemT],
    Insertable[ItemT],
    Poppable[ItemT],
    Protocol,
):
    """Protocol for mutable sequence references.

    Extends SequenceRef with mutation operations.

    Type Parameters:
        CollectionT: Type of this collection (list, tuple, etc)
        ItemT: Type of this collection's item (int, float, str, nested list, dict, etc)
        CollectionValueT: ComputedValue type for this collection (ListType, TupleType, etc)
        ItemValueT: ComputedValue type for this collection's item (IntType, FloatType, etc)
        ViewT: Type of the view at this location
        IndexT: Type of index (commonly int)
        IndexValueT: ComputedValue type for index (commonly IntType)
        SliceValueT: ComputedValue type for sliced result

    Example:
        >>> if isinstance(ref, MutableSequenceRef):
        ...     ref.append(new_item).execute(ctx)
        ...     ref.pop().execute(ctx)
    """

    pass


# =============================================================================
# MAPPING PROTOCOLS
# =============================================================================


@runtime_checkable
class MappingRef[
    CollectionT,
    KeyT,
    ValueT,
    CollectionValueT,
    KeyValueT,
    ValueValueT,
    ViewT,
    ChildRefT,
](
    CollectionRef[CollectionT, ValueT, CollectionValueT, ValueValueT, ViewT],
    Nestable[KeyT, ChildRefT],
    KeysQueryable[KeyT],
    ValuesQueryable[ValueT],
    ItemsQueryable[KeyT, ValueT],
    MappingAccessible[KeyT, ValueT],
    Protocol,
):
    """Protocol for read-only mapping references.

    Mapping refs point to dict-like containers.
    They support key access, keys/values/items queries, extraction, and direct
    container-level get/set/remove operations.

    Type Parameters:
        CollectionT: Type of this collection (dict, etc)
        KeyT: Type of keys (str, int, etc)
        ValueT: Type of values (int, float, nested dict, etc)
        CollectionValueT: ComputedValue type for this collection (DictType, etc)
        KeyValueT: ComputedValue type for keys (StrType, IntType, etc)
        ValueValueT: ComputedValue type for values (IntType, FloatType, AnyType, etc)
        ViewT: Type of the view at this location
        ChildRefT: Type of child reference returned by __getitem__

    Example:
        >>> if isinstance(ref, MappingRef):
        ...     item_ref = ref["key"]
        ...     all_keys = ref.keys().execute(ctx)
        ...     all_items = ref.items().execute(ctx)
        ...     value = ref.get_item("key", "default").execute(ctx)
        ...     ref.set_item("key", "value").execute(ctx)
        ...     ref.remove_item("key").execute(ctx)
    """

    @property
    def key_type(self) -> type[KeyT]:
        """Get the key type for this mapping.

        Returns:
            Type of keys (str, int, etc)
        """
        ...

    @property
    def value_type(self) -> type[ValueT]:
        """Get the value type for this mapping.

        Returns:
            Type of values (int, float, nested dict, etc)
        """
        ...

    @property
    def key_value_type(self) -> type[KeyValueT]:
        """Get the ComputedValue type for this mapping's keys.

        Returns:
            Type of key value (StrType, IntType, etc)
        """
        ...

    @property
    def value_value_type(self) -> type[ValueValueT]:
        """Get the ComputedValue type for this mapping's values.

        Returns:
            Type of value value (IntType, FloatType, AnyType, etc)
        """
        ...


@runtime_checkable
class MutableMappingRef[
    CollectionT,
    KeyT,
    ValueT,
    CollectionValueT,
    KeyValueT,
    ValueValueT,
    ViewT,
    ChildRefT,
](
    MappingRef[
        CollectionT,
        KeyT,
        ValueT,
        CollectionValueT,
        KeyValueT,
        ValueValueT,
        ViewT,
        ChildRefT,
    ],
    Protocol,
):
    """Protocol for mutable mapping references.

    Extends MappingRef with mutation operations.
    Mutations happen through child refs obtained via __getitem__.

    Type Parameters:
        CollectionT: Type of this collection (dict, etc)
        KeyT: Type of keys (str, int, etc)
        ValueT: Type of values (int, float, nested dict, etc)
        CollectionValueT: ComputedValue type for this collection (DictType, etc)
        KeyValueT: ComputedValue type for keys (StrType, IntType, etc)
        ValueValueT: ComputedValue type for values (IntType, FloatType, AnyType, etc)
        ViewT: Type of the view at this location
        ChildRefT: Type of child reference returned by __getitem__

    Example:
        >>> if isinstance(ref, MutableMappingRef):
        ...     ref["new_key"].set(value).execute(ctx)
        ...     ref.clear().execute(ctx)
    """

    pass


# =============================================================================
# SET PROTOCOLS
# =============================================================================


@runtime_checkable
class SetRef[
    CollectionT,
    ItemT,
    CollectionValueT,
    ItemValueT,
    ViewT,
](
    CollectionRef[CollectionT, ItemT, CollectionValueT, ItemValueT, ViewT],
    Protocol,
):
    """Protocol for read-only set references.

    Set refs point to set-like containers.
    They support containment checking, length, and extraction.

    Type Parameters:
        CollectionT: Type of this collection (set, frozenset, etc)
        ItemT: Type of items in the set (int, str, etc)
        CollectionValueT: ComputedValue type for this collection (SetType, etc)
        ItemValueT: ComputedValue type for items (IntType, StrType, etc)
        ViewT: Type of the view at this location

    Example:
        >>> if isinstance(ref, SetRef):
        ...     all_items = ref.extract().execute(ctx)
        ...     size = ref.length().execute(ctx)
    """

    pass


@runtime_checkable
class MutableSetRef[
    CollectionT,
    ItemT,
    CollectionValueT,
    ItemValueT,
    ViewT,
](
    SetRef[CollectionT, ItemT, CollectionValueT, ItemValueT, ViewT],
    Protocol,
):
    """Protocol for mutable set references.

    Extends SetRef with mutation operations.

    Type Parameters:
        CollectionT: Type of this collection (set, etc)
        ItemT: Type of items in the set (int, str, etc)
        CollectionValueT: ComputedValue type for this collection (SetType, etc)
        ItemValueT: ComputedValue type for items (IntType, StrType, etc)
        ViewT: Type of the view at this location

    Example:
        >>> if isinstance(ref, MutableSetRef):
        ...     ref.add(item).execute(ctx)
        ...     ref.remove(item).execute(ctx)
    """

    def add(self, value: ItemT) -> NilType:
        """Create an add command.

        Args:
            value: Item to add

        Returns:
            NilType (add returns None after execution)
        """
        ...

    def remove(self, value: ItemT) -> NilType:
        """Create a remove command.

        Args:
            value: Item to remove

        Returns:
            NilType (remove returns None after execution)
        """
        ...

    def discard(self, value: ItemT) -> NilType:
        """Create a discard command.

        Args:
            value: Item to discard (no error if absent)

        Returns:
            NilType (discard returns None after execution)
        """
        ...


# =============================================================================
# PRIMITIVE REF PROTOCOLS
# =============================================================================


@runtime_checkable
class CollectionItemRef[T, ValueT](
    Existable,
    Gettable,
    Settable,
    Deletable,
    RefObservable,
    Protocol,
):
    """Protocol for primitive (leaf) item references.

    Primitive refs point to single values like int, str, float.
    They support read, write, delete, and observation.

    Type Parameters:
        T: Type of the value at this location (int, str, float, etc)
        ValueT: ComputedValue type for this value (IntType, StrType, FloatType, etc)

    Example:
        >>> if isinstance(ref, CollectionItemRef):
        ...     get_op = ref.get()
        ...     set_cmd = ref.set(new_value)
        ...     delete_cmd = ref.remove()
    """

    @property
    def value_type(self) -> type[T]:
        """Get the value type at this location.

        Returns:
            Type of value stored (int, str, float, etc)
        """
        ...

    @property
    def value_value_type(self) -> type[ValueT]:
        """Get the ComputedValue type for this value.

        Returns:
            Type of computed value (IntType, StrType, FloatType, etc)
        """
        ...
