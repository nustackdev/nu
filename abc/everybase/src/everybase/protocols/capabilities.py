"""Storage capability protocols.

These protocols define optional capabilities for references.
Not all refs support all operations - check protocol support before use.

The capability hierarchy enables composition:
- Read operations (gettable, extractable)
- Write operations (settable, storable, appendable)
- Delete operations (deletable, clearable)
- Existence checks (existable)
- Observable operations (observable, child-observable)
- Navigation (nestable, indexable)

Example:
    >>> if isinstance(ref, Gettable):
    ...     value = ref.get(ctx)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeGuard, runtime_checkable


if TYPE_CHECKING:
    from every import Context, Morphism, Sentinel, Term


__all__ = [  # noqa: RUF022
    # Read capabilities
    "Gettable",
    "Extractable",
    # Write capabilities
    "Settable",
    "Storable",
    "Appendable",
    "Insertable",
    # Delete capabilities
    "Deletable",
    "Clearable",
    "Poppable",
    # Existence capabilities
    "Existable",
    # Observable capabilities
    "RefObservable",
    "RefChildObservable",
    "RefDescendantsObservable",
    # Navigation capabilities
    "Nestable",
    "RefIndexable",
    "RefSliceable",
    # Query capabilities
    "Lengthable",
    "KeysQueryable",
    "ValuesQueryable",
    "ItemsQueryable",
    # Mapping access capabilities
    "MappingAccessible",
    # Type guards
    "is_gettable",
    "is_extractable",
    "is_settable",
    "is_storable",
    "is_deletable",
    "is_clearable",
    "is_existable",
    "is_ref_observable",
    "is_ref_indexable",
    "is_lengthable",
    "is_mapping_accessible",
]


# =============================================================================
# READ CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Gettable[T](Protocol):
    """Protocol for refs that support reading a value.

    Used for value references.
    Returns the value at this location when get() is called.

    Type Parameters:
        T: Type of value at this location

    Example:
        >>> if isinstance(ref, Gettable):
        ...     value = ref.get(ctx)
    """

    def get(self, ctx: Context) -> T | Sentinel:
        """Get value at this location.

        Args:
            ctx: Execution context

        Returns:
            Value at this location, or Sentinel if absent/invalid
        """
        ...


@runtime_checkable
class Extractable[CollectionT](Protocol):
    """Protocol for refs that support extracting entire structures.

    Used for container references.
    Returns the full structure when extract() is called.

    Type Parameters:
        CollectionT: Type of the collection (list, dict, etc.)

    Example:
        >>> if isinstance(ref, Extractable):
        ...     data = ref.extract(ctx)
    """

    def extract(self, ctx: Context) -> CollectionT | Sentinel:
        """Extract entire structure at this location.

        Args:
            ctx: Execution context

        Returns:
            Full collection at this location
        """
        ...


# =============================================================================
# WRITE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Settable[T](Protocol):
    """Protocol for refs that support writing a single value.

    Used for primitive value references.

    Type Parameters:
        T: Type of value to write

    Example:
        >>> if isinstance(ref, Settable):
        ...     ref.set(ctx, new_value)
    """

    def set(self, ctx: Context, value: T | Term) -> None:
        """Set value at this location.

        Args:
            ctx: Execution context
            value: Value to write (literal or Term)
        """
        ...


@runtime_checkable
class Storable[CollectionT](Protocol):
    """Protocol for refs that support storing entire structures.

    Used for container references.

    Type Parameters:
        CollectionT: Type of collection to store (dict, list, etc.)

    Example:
        >>> if isinstance(ref, Storable):
        ...     ref.store(ctx, {"key": "value"})
    """

    def store(self, ctx: Context, value: CollectionT | Term) -> None:
        """Store entire structure at this location.

        Args:
            ctx: Execution context
            value: Collection to store (literal or Term)
        """
        ...


@runtime_checkable
class Appendable[ItemT](Protocol):
    """Protocol for refs that support appending items.

    Used for sequence references.

    Type Parameters:
        ItemT: Type of item to append

    Example:
        >>> if isinstance(ref, Appendable):
        ...     ref.append(ctx, new_item)
    """

    def append(self, ctx: Context, value: ItemT | Term) -> None:
        """Append item to this sequence.

        Args:
            ctx: Execution context
            value: Item to append (literal or Term)
        """
        ...


@runtime_checkable
class Insertable[ItemT](Protocol):
    """Protocol for refs that support inserting items at index.

    Used for sequence references.

    Type Parameters:
        ItemT: Type of item to insert

    Example:
        >>> if isinstance(ref, Insertable):
        ...     ref.insert(ctx, 0, new_item)
    """

    def insert(self, ctx: Context, index: int | Term, value: ItemT | Term) -> None:
        """Insert item at index in this sequence.

        Args:
            ctx: Execution context
            index: Position to insert at
            value: Item to insert (literal or Term)
        """
        ...


# =============================================================================
# DELETE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Deletable(Protocol):
    """Protocol for refs that support deletion.

    Used for primitive and container item references.

    Example:
        >>> if isinstance(ref, Deletable):
        ...     ref.remove(ctx)
    """

    def remove(self, ctx: Context) -> None:
        """Remove value at this location.

        Args:
            ctx: Execution context
        """
        ...


@runtime_checkable
class Clearable(Protocol):
    """Protocol for refs that support clearing all items.

    Used for container references.

    Example:
        >>> if isinstance(ref, Clearable):
        ...     ref.clear(ctx)
    """

    def clear(self, ctx: Context) -> None:
        """Clear all items from this container.

        Args:
            ctx: Execution context
        """
        ...


@runtime_checkable
class Poppable[ItemT](Protocol):
    """Protocol for refs that support popping items.

    Used for sequence references.

    Type Parameters:
        ItemT: Type of item to pop

    Example:
        >>> if isinstance(ref, Poppable):
        ...     removed = ref.pop(ctx)
    """

    def pop(self, ctx: Context, index: int | Term = -1) -> ItemT | Sentinel:
        """Pop and return item from this sequence.

        Args:
            ctx: Execution context
            index: Position to pop from (default: last)

        Returns:
            Removed item
        """
        ...


# =============================================================================
# EXISTENCE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Existable(Protocol):
    """Protocol for refs that support existence checking.

    Example:
        >>> if isinstance(ref, Existable):
        ...     if ref.exists(ctx):
        ...         print("Ref exists")
    """

    def exists(self, ctx: Context) -> bool:
        """Check if this location exists.

        Args:
            ctx: Execution context

        Returns:
            True if location exists
        """
        ...

    def missing(self, ctx: Context) -> bool:
        """Check if this location is missing.

        Args:
            ctx: Execution context

        Returns:
            True if location doesn't exist
        """
        ...


# =============================================================================
# OBSERVABLE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class RefObservable(Protocol):
    """Protocol for refs that support observing changes.

    Example:
        >>> if isinstance(ref, RefObservable):
        ...     subscription = ref.on_change(callback)
    """

    def on_change(self, callback: Any) -> Morphism:  # noqa: ANN401
        """Subscribe to changes at this location.

        Args:
            callback: Function to call on changes

        Returns:
            Subscription morphism
        """
        ...


@runtime_checkable
class RefChildObservable[KeyT](Protocol):
    """Protocol for refs that support observing child changes.

    Type Parameters:
        KeyT: Type of child address/key

    Example:
        >>> if isinstance(ref, RefChildObservable):
        ...     subscription = ref.on_child_change("key", callback)
    """

    def on_child_change(self, address: KeyT | Term, callback: Any) -> Morphism:  # noqa: ANN401
        """Subscribe to changes at a child location.

        Args:
            address: Child address to watch
            callback: Function to call on changes

        Returns:
            Subscription morphism
        """
        ...

    def on_children_change(self, callback: Any) -> Morphism:  # noqa: ANN401
        """Subscribe to changes at any child location.

        Args:
            callback: Function to call on changes

        Returns:
            Subscription morphism
        """
        ...


@runtime_checkable
class RefDescendantsObservable(Protocol):
    """Protocol for refs that support observing descendant changes.

    Example:
        >>> if isinstance(ref, RefDescendantsObservable):
        ...     subscription = ref.on_descendants_change("*", "status", callback)
    """

    def on_descendants_change(self, *pattern: str | int, callback: Any) -> Morphism:  # noqa: ANN401
        """Subscribe to changes at descendant locations.

        Args:
            *pattern: Key pattern (use "*" for wildcards)
            callback: Function to call on changes

        Returns:
            Subscription morphism
        """
        ...


# =============================================================================
# NAVIGATION CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Nestable[KeyT, RefT](Protocol):
    """Protocol for refs that support navigation to children.

    Used for container references to navigate to nested locations.

    Type Parameters:
        KeyT: Type of child address/key
        RefT: Type of child reference returned

    Example:
        >>> if isinstance(ref, Nestable):
        ...     child_ref = ref["key"]
    """

    def __getitem__(self, key: KeyT | Term) -> RefT:
        """Navigate to child location.

        Args:
            key: Child address/key

        Returns:
            Reference to child location
        """
        ...


@runtime_checkable
class RefIndexable[IndexT, RefT](Protocol):
    """Protocol for refs that support index-based access.

    Type Parameters:
        IndexT: Type of index (typically int)
        RefT: Type of item reference returned

    Example:
        >>> if isinstance(ref, RefIndexable):
        ...     item_ref = ref[0]
    """

    def __getitem__(self, key: IndexT | Term) -> RefT:
        """Get reference to item at index.

        Args:
            key: Index value

        Returns:
            Reference to item at index
        """
        ...


@runtime_checkable
class RefSliceable[RefT](Protocol):
    """Protocol for refs that support slicing.

    Type Parameters:
        RefT: Type of slice reference returned

    Example:
        >>> if isinstance(ref, RefSliceable):
        ...     slice_ref = ref[1:5]
    """

    def __getitem__(self, key: slice) -> RefT:
        """Get reference to slice.

        Args:
            key: Slice specification

        Returns:
            Reference to slice
        """
        ...


# =============================================================================
# QUERY CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Lengthable(Protocol):
    """Protocol for refs that support length queries.

    Example:
        >>> if isinstance(ref, Lengthable):
        ...     size = ref.length(ctx)
    """

    def length(self, ctx: Context) -> int:
        """Get length of this container.

        Args:
            ctx: Execution context

        Returns:
            Number of items
        """
        ...


@runtime_checkable
class KeysQueryable[KeyT](Protocol):
    """Protocol for refs that support keys queries.

    Type Parameters:
        KeyT: Type of keys in the mapping

    Example:
        >>> if isinstance(ref, KeysQueryable):
        ...     all_keys = ref.keys(ctx)
    """

    def keys(self, ctx: Context) -> list[KeyT]:
        """Get all keys in this mapping.

        Args:
            ctx: Execution context

        Returns:
            List of all keys
        """
        ...


@runtime_checkable
class ValuesQueryable[ValueT](Protocol):
    """Protocol for refs that support values queries.

    Type Parameters:
        ValueT: Type of values in the mapping

    Example:
        >>> if isinstance(ref, ValuesQueryable):
        ...     all_values = ref.values(ctx)
    """

    def values(self, ctx: Context) -> list[ValueT]:
        """Get all values in this mapping.

        Args:
            ctx: Execution context

        Returns:
            List of all values
        """
        ...


@runtime_checkable
class ItemsQueryable[KeyT, ValueT](Protocol):
    """Protocol for refs that support items queries.

    Type Parameters:
        KeyT: Type of keys in the mapping
        ValueT: Type of values in the mapping

    Example:
        >>> if isinstance(ref, ItemsQueryable):
        ...     all_items = ref.items(ctx)
    """

    def items(self, ctx: Context) -> list[tuple[KeyT, ValueT]]:
        """Get all (key, value) pairs in this mapping.

        Args:
            ctx: Execution context

        Returns:
            List of all items
        """
        ...


# =============================================================================
# MAPPING ACCESS CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class MappingAccessible[KeyT, ValueT](Protocol):
    """Protocol for refs that support direct mapping access operations.

    Provides get_item(), set_item(), and remove_item() for accessing mapping
    containers directly without navigating to child refs.

    Type Parameters:
        KeyT: Type of keys in the mapping
        ValueT: Type of values in the mapping

    Example:
        >>> if isinstance(ref, MappingAccessible):
        ...     value = ref.get_item(ctx, "key", "default")
        ...     ref.set_item(ctx, "key", "value")
        ...     ref.remove_item(ctx, "key")
    """

    def get_item(
        self,
        ctx: Context,
        key: KeyT | Term,
        default: ValueT | Sentinel | None = None,
    ) -> ValueT | Sentinel:
        """Get value by key with optional default.

        Args:
            ctx: Execution context
            key: Key to look up
            default: Value to return if key not found

        Returns:
            Value at key or default
        """
        ...

    def set_item(
        self,
        ctx: Context,
        key: KeyT | Term,
        value: ValueT | Term,
    ) -> None:
        """Set value at key in mapping.

        Args:
            ctx: Execution context
            key: Key to set
            value: Value to set (literal or Term)
        """
        ...

    def remove_item(self, ctx: Context, key: KeyT | Term) -> None:
        """Remove key from mapping.

        Args:
            ctx: Execution context
            key: Key to remove
        """
        ...


# =============================================================================
# TYPE GUARDS
# =============================================================================


def is_gettable(obj: object) -> TypeGuard[Gettable]:
    """Check if object supports get operation."""
    return isinstance(obj, Gettable)


def is_extractable(obj: object) -> TypeGuard[Extractable]:
    """Check if object supports extract operation."""
    return isinstance(obj, Extractable)


def is_settable(obj: object) -> TypeGuard[Settable]:
    """Check if object supports set operation."""
    return isinstance(obj, Settable)


def is_storable(obj: object) -> TypeGuard[Storable]:
    """Check if object supports store operation."""
    return isinstance(obj, Storable)


def is_deletable(obj: object) -> TypeGuard[Deletable]:
    """Check if object supports delete operation."""
    return isinstance(obj, Deletable)


def is_clearable(obj: object) -> TypeGuard[Clearable]:
    """Check if object supports clear operation."""
    return isinstance(obj, Clearable)


def is_existable(obj: object) -> TypeGuard[Existable]:
    """Check if object supports existence check."""
    return isinstance(obj, Existable)


def is_ref_observable(obj: object) -> TypeGuard[RefObservable]:
    """Check if object supports change observation."""
    return isinstance(obj, RefObservable)


def is_ref_indexable(obj: object) -> TypeGuard[RefIndexable]:
    """Check if object supports index-based access."""
    return isinstance(obj, RefIndexable)


def is_lengthable(obj: object) -> TypeGuard[Lengthable]:
    """Check if object supports length queries."""
    return isinstance(obj, Lengthable)


def is_mapping_accessible(obj: object) -> TypeGuard[MappingAccessible]:
    """Check if object supports direct mapping access operations."""
    return isinstance(obj, MappingAccessible)
