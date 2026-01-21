"""Collection reference protocol hierarchy.

This module defines collection ref protocols composed from atomic capabilities.
Follows Python's collections.abc hierarchy while using capability composition.

These are PROTOCOLS (type contracts) that define what refs CAN do.

Protocol Hierarchy:
    ContainerRef (existence checking)
    └── CollectionRef (sized, extractable, storable)
        ├── SequenceRef[T] (indexed access)
        │   └── MutableSequenceRef[T]
        ├── MappingRef[K,V] (key access)
        │   └── MutableMappingRef[K,V]
        └── SetRef[T] (containment)
            └── MutableSetRef[T]
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
    from every import Context


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
    "SetLikeRef",
    "MutableSetLikeRef",
    # Item protocol
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
        ViewT: Type of the view at this location

    Example:
        >>> if isinstance(ref, ContainerRef):
        ...     if ref.exists(ctx):
        ...         print("Ref exists")
    """

    @property
    def view_type(self) -> type[ViewT]:
        """Get the view type for this container."""
        ...


@runtime_checkable
class CollectionRef[CollectionT, ItemT, ViewT](
    ContainerRef[ViewT],
    Extractable[CollectionT],
    Storable[CollectionT],
    Clearable,
    Lengthable,
    Protocol,
):
    """Protocol for sized collection refs.

    Foundation protocol for all collection refs (sequences, mappings, sets).
    Supports extraction, storage, clearing, and length queries.

    Type Parameters:
        CollectionT: Type of this collection (dict, list, etc)
        ItemT: Type of this collection's item
        ViewT: Type of the view at this location

    Example:
        >>> if isinstance(ref, CollectionRef):
        ...     data = ref.extract(ctx)
        ...     ref.store(ctx, new_data)
        ...     length = ref.length(ctx)
    """

    @property
    def item_type(self) -> type[ItemT]:
        """Get the item type for this collection."""
        ...

    @property
    def collection_type(self) -> type[CollectionT]:
        """Get the collection type."""
        ...


# =============================================================================
# SEQUENCE PROTOCOLS
# =============================================================================


@runtime_checkable
class SequenceRef[CollectionT, ItemT, ViewT, IndexT, ItemRefT](
    CollectionRef[CollectionT, ItemT, ViewT],
    RefIndexable[IndexT, ItemRefT],
    RefSliceable[CollectionT],
    Protocol,
):
    """Protocol for read-only sequence references.

    Sequence refs point to list-like containers.
    They support index access, slicing, length, and extraction.

    Type Parameters:
        CollectionT: Type of this collection (list, tuple, etc)
        ItemT: Type of this collection's item
        ViewT: Type of the view at this location
        IndexT: Type of index (commonly int)
        ItemRefT: Type of item reference returned

    Example:
        >>> if isinstance(ref, SequenceRef):
        ...     first_ref = ref[0]
        ...     first = first_ref.get(ctx)
        ...     slice_ref = ref[1:5]
    """

    @property
    def index_type(self) -> type[IndexT]:
        """Get the index type for this sequence."""
        ...


@runtime_checkable
class MutableSequenceRef[CollectionT, ItemT, ViewT, IndexT, ItemRefT](
    SequenceRef[CollectionT, ItemT, ViewT, IndexT, ItemRefT],
    Appendable[ItemT],
    Insertable[ItemT],
    Poppable[ItemT],
    Protocol,
):
    """Protocol for mutable sequence references.

    Extends SequenceRef with mutation operations.

    Type Parameters:
        CollectionT: Type of this collection (list, etc)
        ItemT: Type of this collection's item
        ViewT: Type of the view at this location
        IndexT: Type of index (commonly int)
        ItemRefT: Type of item reference returned

    Example:
        >>> if isinstance(ref, MutableSequenceRef):
        ...     ref.append(ctx, new_item)
        ...     removed = ref.pop(ctx)
    """

    pass


# =============================================================================
# MAPPING PROTOCOLS
# =============================================================================


@runtime_checkable
class MappingRef[CollectionT, KeyT, ValueT, ViewT, ChildRefT](
    CollectionRef[CollectionT, ValueT, ViewT],
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
        ValueT: Type of values
        ViewT: Type of the view at this location
        ChildRefT: Type of child reference returned by __getitem__

    Example:
        >>> if isinstance(ref, MappingRef):
        ...     item_ref = ref["key"]
        ...     all_keys = ref.keys(ctx)
        ...     value = ref.get_item(ctx, "key", "default")
    """

    @property
    def key_type(self) -> type[KeyT]:
        """Get the key type for this mapping."""
        ...

    @property
    def value_type(self) -> type[ValueT]:
        """Get the value type for this mapping."""
        ...


@runtime_checkable
class MutableMappingRef[CollectionT, KeyT, ValueT, ViewT, ChildRefT](
    MappingRef[CollectionT, KeyT, ValueT, ViewT, ChildRefT],
    Protocol,
):
    """Protocol for mutable mapping references.

    Extends MappingRef with mutation operations.
    Mutations happen through child refs or set_item/remove_item.

    Type Parameters:
        CollectionT: Type of this collection (dict, etc)
        KeyT: Type of keys (str, int, etc)
        ValueT: Type of values
        ViewT: Type of the view at this location
        ChildRefT: Type of child reference returned by __getitem__

    Example:
        >>> if isinstance(ref, MutableMappingRef):
        ...     ref.set_item(ctx, "key", "value")
        ...     ref.clear(ctx)
    """

    pass


# =============================================================================
# SET PROTOCOLS
# =============================================================================


@runtime_checkable
class SetLikeRef[CollectionT, ItemT, ViewT](
    CollectionRef[CollectionT, ItemT, ViewT],
    Protocol,
):
    """Protocol for read-only set references.

    Set refs point to set-like containers.
    They support containment checking, length, and extraction.

    Type Parameters:
        CollectionT: Type of this collection (set, frozenset, etc)
        ItemT: Type of items in the set
        ViewT: Type of the view at this location

    Example:
        >>> if isinstance(ref, SetRef):
        ...     all_items = ref.extract(ctx)
        ...     size = ref.length(ctx)
    """

    pass


@runtime_checkable
class MutableSetLikeRef[CollectionT, ItemT, ViewT](
    SetLikeRef[CollectionT, ItemT, ViewT],
    Protocol,
):
    """Protocol for mutable set references.

    Extends SetRef with mutation operations.

    Type Parameters:
        CollectionT: Type of this collection (set, etc)
        ItemT: Type of items in the set
        ViewT: Type of the view at this location

    Example:
        >>> if isinstance(ref, MutableSetRef):
        ...     ref.add(ctx, item)
        ...     ref.remove(ctx, item)
    """

    def add(self, ctx: Context, value: ItemT) -> None:
        """Add item to this set.

        Args:
            ctx: Execution context
            value: Item to add
        """
        ...

    def remove(self, ctx: Context, value: ItemT) -> None:
        """Remove item from this set.

        Args:
            ctx: Execution context
            value: Item to remove

        Raises:
            KeyError: If item not in set
        """
        ...

    def discard(self, ctx: Context, value: ItemT) -> None:
        """Discard item from this set (no error if absent).

        Args:
            ctx: Execution context
            value: Item to discard
        """
        ...


# =============================================================================
# ITEM REF PROTOCOLS
# =============================================================================


@runtime_checkable
class CollectionItemRef[T](
    Existable,
    Gettable[T],
    Settable[T],
    Deletable,
    RefObservable,
    Protocol,
):
    """Protocol for collection item references.

    Item refs point to single values within collections.
    They support read, write, delete, and observation.

    Type Parameters:
        T: Type of the value at this location

    Example:
        >>> if isinstance(ref, CollectionItemRef):
        ...     value = ref.get(ctx)
        ...     ref.set(ctx, new_value)
        ...     ref.remove(ctx)
    """

    @property
    def value_type(self) -> type[T]:
        """Get the value type at this location."""
        ...
