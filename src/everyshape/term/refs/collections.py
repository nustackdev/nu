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

from typing import Protocol, runtime_checkable

from ..values import IntValue, NoneValue
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
    Nestable,
    Poppable,
    RefIndexable,
    RefObservable,
    RefSliceable,
    Settable,
    Storable,
    ValuesQueryable,
)


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
    # Primitive protocols
    "PrimitiveRef",
    "ValueRef",
]


# =============================================================================
# BASE REF PROTOCOLS
# =============================================================================


@runtime_checkable
class ContainerRef[ViewT](
    Existable[object],
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
    Extractable[CollectionT, CollectionValueT],
    Storable[CollectionT, CollectionValueT],
    Clearable[NoneValue],
    Lengthable[IntValue],
    Protocol,
):
    """Protocol for sized, observable collection refs.

    Foundation protocol for all collection refs (sequences, mappings, sets).
    Supports extraction, storage, clearing, length queries, and observation.

    Type Parameters:
        CollectionT: Type of this collection (dict, list, etc)
        ItemT: Type of this collection's item (int, float, str, nested list, dict, etc)
        CollectionValueT: ComputedValue type for this collection (ListValue, DictValue, etc)
        ItemValueT: ComputedValue type for this collection's item (IntValue, FloatValue, UnknownValue, etc)
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
            Type of items (IntValue, FloatValue, UnknownValue, etc)
        """
        ...

    @property
    def collection_value_type(self) -> type[ItemValueT]:
        """Get the ComputedValue type for this collection.

        Returns:
            Type of collection (DictValue, ListValue, etc)
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
    RefIndexable[IndexT, IndexValueT, ItemValueT],
    RefSliceable[SliceValueT],
    Protocol,
):
    """Protocol for read-only sequence references.

    Sequence refs point to list-like containers.
    They support index access, slicing, length, and extraction.

    Type Parameters:
        IndexT: type of index
        IndexValueT: type of computed value for index
        SliceValueT: type of sliced value

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
            Type of computed value for index (commonly IntValue)
        """
        ...


@runtime_checkable
class MutableSequenceRef[IndexT, ItemT](
    SequenceRef[IndexT, ItemT],
    Appendable[ItemT, object],
    Insertable[ItemT, object],
    Poppable[ItemT, object],
    Protocol,
):
    """Protocol for mutable sequence references.

    Extends SequenceRef with mutation operations.

    Type Parameters:
        T: Type of items in the sequence

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
class MappingRef[K, V](
    CollectionRef[V, object],
    Nestable[K, object],
    KeysQueryable[object],
    ValuesQueryable[object],
    ItemsQueryable[object],
    Protocol,
):
    """Protocol for read-only mapping references.

    Mapping refs point to dict-like containers.
    They support key access, keys/values/items queries, and extraction.

    Type Parameters:
        K: Type of keys
        V: Type of values

    Example:
        >>> if isinstance(ref, MappingRef):
        ...     item_ref = ref["key"]
        ...     all_keys = ref.keys().execute(ctx)
        ...     all_items = ref.items().execute(ctx)
    """

    @property
    def key_type(self) -> type[K]:
        """Get the key type for this mapping.

        Returns:
            Type of keys
        """
        ...

    @property
    def value_type(self) -> type[V]:
        """Get the value type for this mapping.

        Returns:
            Type of values
        """
        ...


@runtime_checkable
class MutableMappingRef[K, V](
    MappingRef[K, V],
    Protocol,
):
    """Protocol for mutable mapping references.

    Extends MappingRef with mutation operations.
    Mutations happen through child refs obtained via __getitem__.

    Type Parameters:
        K: Type of keys
        V: Type of values

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
class SetRef[T](
    CollectionRef[object],
    Protocol,
):
    """Protocol for read-only set references.

    Set refs point to set-like containers.
    They support containment checking, length, and extraction.

    Type Parameters:
        T: Type of items in the set

    Example:
        >>> if isinstance(ref, SetRef):
        ...     all_items = ref.extract().execute(ctx)
        ...     size = ref.length().execute(ctx)
    """

    @property
    def item_type(self) -> type[T]:
        """Get the item type for this set.

        Returns:
            Type of items
        """
        ...


@runtime_checkable
class MutableSetRef[T, PathT](
    SetRef[T, PathT],
    Protocol,
):
    """Protocol for mutable set references.

    Extends SetRef with mutation operations.

    Type Parameters:
        T: Type of items in the set

    Example:
        >>> if isinstance(ref, MutableSetRef):
        ...     ref.add(item).execute(ctx)
        ...     ref.remove(item).execute(ctx)
    """

    def add(self, value: T) -> object:
        """Create an add command.

        Args:
            value: Item to add

        Returns:
            AddCmd that adds the item when executed
        """
        ...

    def remove(self, value: T) -> object:
        """Create a remove command.

        Args:
            value: Item to remove

        Returns:
            RemoveCmd that removes the item when executed
        """
        ...

    def discard(self, value: T) -> object:
        """Create a discard command.

        Args:
            value: Item to discard (no error if absent)

        Returns:
            DiscardCmd that discards the item when executed
        """
        ...


# =============================================================================
# PRIMITIVE REF PROTOCOLS
# =============================================================================


@runtime_checkable
class PrimitiveRef[T, PathT](
    Existable[object],
    Gettable[T, object],
    Settable[T, object],
    Deletable[object],
    RefObservable[object],
    Protocol,
):
    """Protocol for primitive (leaf) value references.

    Primitive refs point to single values like int, str, float.
    They support read, write, delete, and observation.

    Type Parameters:
        T: Type of the value at this location

    Example:
        >>> if isinstance(ref, PrimitiveRef):
        ...     get_op = ref.get()
        ...     set_cmd = ref.set(new_value)
        ...     delete_cmd = ref.remove()
    """

    pass


@runtime_checkable
class ValueRef[T, PathT](
    PrimitiveRef[T, PathT],
    Protocol,
):
    """Protocol for typed value references.

    Extends PrimitiveRef with value type information.

    Type Parameters:
        T: Type of the value at this location

    Example:
        >>> ref: ValueRef[int, Path]
        >>> val = ref.get().execute(ctx)  # Returns int
    """

    @property
    def value_type(self) -> type[T]:
        """Get the value type at this location.

        Returns:
            Type of value stored
        """
        ...
