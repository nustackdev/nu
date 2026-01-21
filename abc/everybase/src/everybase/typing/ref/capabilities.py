"""LValue capability protocols.

These protocols define optional capabilities for LValue references.
Not all LValues support all operations - check protocol support before use.

The capability hierarchy enables composition:
- Read operations (gettable, extractable)
- Write operations (settable, storable, appendable)
- Delete operations (deletable, clearable)
- Existence checks (existable)
- Observable operations (observable, child-observable)
- Navigation (nestable, indexable)

LValues differ from Terms:
- LValues are LOCATIONS in storage (lazy access)
- Terms are ALREADY COMPUTED values in memory

Example:
    >>> if isinstance(ref, Gettable):
    ...     get_op = ref.get()  # Creates GetOp
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeGuard, runtime_checkable


if TYPE_CHECKING:
    from every import Computation, Sentinel, Term
    from everybase.types import BoolType, IntType, ListType, NoneType


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
class Gettable[ValueT](Protocol):
    """Protocol for LValues that support reading a single value.

    Used for primitive value references (ValueRef).
    Returns a ComputedValue that reads the value when executed.

    Type Parameters:
        ValueT: Type of value at this location

    Example:
        >>> if isinstance(ref, Gettable):
        ...     value_op = ref.get()
        ...     value = value_op.execute(ctx)
    """

    def get(
        self,
    ) -> ValueT:
        """Create a get operation for this location.

        Returns:
            ComputedValue that reads the value when executed
        """
        ...


@runtime_checkable
class Extractable[CollectionValueT](Protocol):
    """Protocol for LValues that support extracting entire structures.

    Used for container references (ViewRef).
    Returns a ComputedValue that reads the full structure when executed.

    Type Parameters:
        CollectionValueT: ComputedValue type for the collection (ListType, DictType, etc.)

    Example:
        >>> if isinstance(ref, Extractable):
        ...     extract_op = ref.extract()
        ...     data = extract_op.execute(ctx)  # Returns dict/list/etc
    """

    def extract(self) -> CollectionValueT:
        """Create an extract operation for this container.

        Returns:
            ComputedValue that extracts entire structure when executed
        """
        ...


# =============================================================================
# WRITE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Settable[ValueT](Protocol):
    """Protocol for LValues that support writing a single value.

    Used for primitive value references.
    Returns a ComputedValue that writes the value when executed.

    Type Parameters:
        ValueT: Type of value to write

    Example:
        >>> if isinstance(ref, Settable):
        ...     set_cmd = ref.set(new_value)
        ...     set_cmd.execute(ctx)
    """

    def set(
        self, value: ValueT | Term
    ) -> object:  # Returns ComputedValue type based on ValueT (IntType, StrType, etc.)
        """Create a set command for this location.

        Args:
            value: Value to write (literal or Term)

        Returns:
            ComputedValue that writes the value when executed
        """
        ...


@runtime_checkable
class Storable[CollectionT, CollectionValueT](Protocol):
    """Protocol for LValues that support storing entire structures.

    Used for container references.
    Returns a ComputedValue that writes the entire structure when executed.

    Type Parameters:
        CollectionT: Type of value to store (dict, list, etc.)
        CollectionValueT: ComputedValue type for the collection (ListType, DictType, etc.)

    Example:
        >>> if isinstance(ref, Storable):
        ...     store_cmd = ref.store({"key": "value"})
        ...     store_cmd.execute(ctx)
    """

    def store(self, value: CollectionT | Term) -> CollectionValueT:
        """Create a store command for this container.

        Args:
            value: Value to store (literal or Term)

        Returns:
            StoreCmd that stores the value when executed
        """
        ...


@runtime_checkable
class Appendable[ItemT](Protocol):
    """Protocol for LValues that support appending items.

    Used for sequence references.
    Returns a ComputedValue (NoneType) that appends the item when executed.

    Type Parameters:
        ItemT: Type of item to append

    Example:
        >>> if isinstance(ref, Appendable):
        ...     append_cmd = ref.append(new_item)
        ...     append_cmd.execute(ctx)
    """

    def append(self, value: ItemT | Term) -> NoneType:
        """Create an append command.

        Args:
            value: Item to append (literal or Term)

        Returns:
            AppendCmd that appends the item when executed
        """
        ...


@runtime_checkable
class Insertable[ItemT](Protocol):
    """Protocol for LValues that support inserting items at index.

    Used for sequence references.
    Returns a ComputedValue (NoneType) that inserts the item when executed.

    Type Parameters:
        ItemT: Type of item to insert

    Example:
        >>> if isinstance(ref, Insertable):
        ...     insert_cmd = ref.insert(0, new_item)
        ...     insert_cmd.execute(ctx)
    """

    def insert(self, index: int | Term, value: ItemT | Term) -> NoneType:
        """Create an insert command.

        Args:
            index: Position to insert at
            value: Item to insert (literal or Term)

        Returns:
            InsertCmd that inserts the item when executed
        """
        ...


# =============================================================================
# DELETE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Deletable(Protocol):
    """Protocol for LValues that support deletion.

    Used for primitive and container item references.
    Returns a ComputedValue (NoneType) that removes the value when executed.

    Example:
        >>> if isinstance(ref, Deletable):
        ...     delete_cmd = ref.remove()
        ...     delete_cmd.execute(ctx)
    """

    def remove(self) -> NoneType:
        """Create a delete command for this location.

        Returns:
            DeleteCmd that removes the value when executed
        """
        ...


@runtime_checkable
class Clearable(Protocol):
    """Protocol for LValues that support clearing all items.

    Used for container references.
    Returns a ComputedValue (NoneType) that removes all items when executed.

    Example:
        >>> if isinstance(ref, Clearable):
        ...     clear_cmd = ref.clear()
        ...     clear_cmd.execute(ctx)
    """

    def clear(self) -> NoneType:
        """Create a clear command for this container.

        Returns:
            ClearCmd that clears all items when executed
        """
        ...


@runtime_checkable
class Poppable[ItemValueT](Protocol):
    """Protocol for LValues that support popping items.

    Used for sequence references.
    Returns a ComputedValue that removes and returns an item when executed.

    Type Parameters:
        ItemValueT: Type value of item to pop

    Example:
        >>> if isinstance(ref, Poppable):
        ...     pop_cmd = ref.pop()
        ...     removed = pop_cmd.execute(ctx)
    """

    def pop(
        self, index: int | Term[int | Sentinel] = -1
    ) -> ItemValueT:  # Return type depends on ItemT
        """Create a pop command.

        Args:
            index: Position to pop from (default: last)

        Returns:
            PopCmd that removes and returns the item when executed
        """
        ...


# =============================================================================
# EXISTENCE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Existable(Protocol):
    """Protocol for LValues that support existence checking.

    Returns ComputedValue (BoolType) that checks if the location exists.

    Example:
        >>> if isinstance(ref, Existable):
        ...     exists_op = ref.exists()
        ...     does_exist = exists_op.execute(ctx)
    """

    def exists(self) -> BoolType:
        """Create an existence check operation.

        Returns:
            BoolType that returns True if location exists
        """
        ...

    def missing(self) -> BoolType:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if location doesn't exist
        """
        ...


# =============================================================================
# OBSERVABLE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class RefObservable(Protocol):
    """Protocol for LValues that support observing changes.

    Returns operations that create subscriptions to changes.

    Type Parameters:
        OpT: Type of the operation returned

    Example:
        >>> if isinstance(ref, RefObservable):
        ...     change_op = ref.on_change()
        ...     subscription = change_op.execute(ctx)
    """

    def on_change(self) -> Computation:
        """Create a change subscription operation.

        Returns:
            OnChangeOp that creates subscription when executed
        """
        ...


@runtime_checkable
class RefChildObservable[KeyT](Protocol):
    """Protocol for LValues that support observing child changes.

    Type Parameters:
        KeyT: Type of child address/key
        OpT: Type of the operation returned

    Example:
        >>> if isinstance(ref, RefChildObservable):
        ...     child_op = ref.on_child_change("key")
        ...     subscription = child_op.execute(ctx)
    """

    def on_child_change(self, address: KeyT | Term) -> Computation:
        """Create a child change subscription operation.

        Args:
            address: Child address to watch

        Returns:
            OnChildChangeOp that creates subscription when executed
        """
        ...

    def on_children_change(self) -> Computation:
        """Create a children change subscription operation.

        Returns:
            OnChildrenChangeOp that creates subscription when executed
        """
        ...


@runtime_checkable
class RefDescendantsObservable(Protocol):
    """Protocol for LValues that support observing descendant changes.

    Type Parameters:
        OpT: Type of the operation returned

    Example:
        >>> if isinstance(ref, RefDescendantsObservable):
        ...     desc_op = ref.on_descendants_change("*", "status")
        ...     subscription = desc_op.execute(ctx)
    """

    def on_descendants_change(self, *pattern: str | int) -> Computation:
        """Create a descendants change subscription operation.

        Args:
            *pattern: Key pattern (use "*" for wildcards)

        Returns:
            OnDescendantsChangeOp that creates subscription when executed
        """
        ...


# =============================================================================
# NAVIGATION CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Nestable[KeyT, RefT](Protocol):
    """Protocol for LValues that support navigation to children.

    Used for container references to navigate to nested locations.

    Type Parameters:
        KeyT: Type of child address/key
        RefT: Type of child reference returned

    Example:
        >>> if isinstance(ref, Nestable):
        ...     child_ref = ref["key"]  # Navigate to child
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
    """Protocol for LValues that support index-based access.

    Type Parameters:
        IndexT: Type of index (typically int)
        RefT: Type of item reference returned

    Example:
        >>> if isinstance(ref, RefIndexable):
        ...     item_ref = ref[0]  # Get first item reference
    """

    def __getitem__(self, key: IndexT | Term[IndexT | Sentinel]) -> RefT:
        """Get reference to item at index.

        Args:
            key: Index value

        Returns:
            Reference to item at index
        """
        ...


@runtime_checkable
class RefSliceable[RefT](Protocol):
    """Protocol for LValues that support slicing.

    Type Parameters:
        RefT: Type of slice reference returned

    Example:
        >>> if isinstance(ref, RefSliceable):
        ...     slice_ref = ref[1:5]  # Get slice reference
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
    """Protocol for LValues that support length queries.

    Example:
        >>> if isinstance(ref, Lengthable):
        ...     len_op = ref.length()
        ...     size = len_op.execute(ctx)
    """

    def length(self) -> IntType:
        """Create a length query operation.

        Returns:
            LengthOp that returns the length when executed
        """
        ...


@runtime_checkable
class KeysQueryable[KeyT](Protocol):
    """Protocol for LValues that support keys queries.

    Type Parameters:
        KeyT: Type of keys in the mapping

    Example:
        >>> if isinstance(ref, KeysQueryable):
        ...     keys_op = ref.keys()
        ...     all_keys = keys_op.execute(ctx)
    """

    def keys(self) -> ListType[KeyT]:
        """Create a keys query operation.

        Returns:
            ListType that returns all keys when executed
        """
        ...


@runtime_checkable
class ValuesQueryable[ValueT](Protocol):
    """Protocol for LValues that support values queries.

    Type Parameters:
        ValueT: Type of values in the mapping

    Example:
        >>> if isinstance(ref, ValuesQueryable):
        ...     values_op = ref.values()
        ...     all_values = values_op.execute(ctx)
    """

    def values(self) -> ListType[ValueT]:
        """Create a values query operation.

        Returns:
            ListType that returns all values when executed
        """
        ...


@runtime_checkable
class ItemsQueryable[KeyT, ValueT](Protocol):
    """Protocol for LValues that support items queries.

    Type Parameters:
        KeyT: Type of keys in the mapping
        ValueT: Type of values in the mapping

    Example:
        >>> if isinstance(ref, ItemsQueryable):
        ...     items_op = ref.items()
        ...     all_items = items_op.execute(ctx)
    """

    def items(self) -> ListType[tuple[KeyT, ValueT]]:
        """Create an items query operation.

        Returns:
            ItemsOp that returns all (key, value) pairs when executed
        """
        ...


# =============================================================================
# MAPPING ACCESS CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class MappingAccessible[KeyT, ValueT](Protocol):
    """Protocol for LValues that support direct mapping access operations.

    Provides get(), set_item(), and remove_item() for accessing mapping
    containers directly without navigating to child refs.

    Type Parameters:
        KeyT: Type of keys in the mapping
        ValueT: Type of values in the mapping

    Example:
        >>> if isinstance(ref, MappingAccessible):
        ...     value = ref.get_item("key", "default").execute(ctx)
        ...     ref.set_item("key", "value").execute(ctx)
        ...     ref.remove_item("key").execute(ctx)
    """

    def get_item(
        self,
        key: KeyT | Term,
        default: ValueT | Sentinel | None = None,
    ) -> object:  # Returns ComputedValue type based on ValueT
        """Get value by key with optional default.

        Args:
            key: Key to look up
            default: Value to return if key not found (default: Empty)

        Returns:
            ComputedValue containing value at key or default
        """
        ...

    def set_item(
        self,
        key: KeyT | Term,
        value: ValueT | Term,
    ) -> object:  # Returns ComputedValue type based on ValueT
        """Set value at key in mapping.

        Args:
            key: Key to set
            value: Value to set (literal or Term)

        Returns:
            ComputedValue containing the set value
        """
        ...

    def remove_item(self, key: KeyT | Term) -> NoneType:
        """Remove key from mapping.

        Args:
            key: Key to remove

        Returns:
            NoneType (remove returns None after execution)

        Note:
            Raises KeyError at execution if key not found.
        """
        ...


# =============================================================================
# TYPE GUARDS
# =============================================================================


def is_gettable(obj: object) -> TypeGuard[Gettable]:
    """Check if object supports get operation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Gettable protocol
    """
    return isinstance(obj, Gettable)


def is_extractable(obj: object) -> TypeGuard[Extractable]:
    """Check if object supports extract operation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Extractable protocol
    """
    return isinstance(obj, Extractable)


def is_settable(obj: object) -> TypeGuard[Settable]:
    """Check if object supports set operation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Settable protocol
    """
    return isinstance(obj, Settable)


def is_storable(obj: object) -> TypeGuard[Storable]:
    """Check if object supports store operation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Storable protocol
    """
    return isinstance(obj, Storable)


def is_deletable(obj: object) -> TypeGuard[Deletable]:
    """Check if object supports delete operation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Deletable protocol
    """
    return isinstance(obj, Deletable)


def is_clearable(obj: object) -> TypeGuard[Clearable]:
    """Check if object supports clear operation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Clearable protocol
    """
    return isinstance(obj, Clearable)


def is_existable(obj: object) -> TypeGuard[Existable]:
    """Check if object supports existence check.

    Args:
        obj: Object to check

    Returns:
        True if object implements Existable protocol
    """
    return isinstance(obj, Existable)


def is_ref_observable(obj: object) -> TypeGuard[RefObservable]:
    """Check if object supports change observation.

    Args:
        obj: Object to check

    Returns:
        True if object implements RefObservable protocol
    """
    return isinstance(obj, RefObservable)


def is_ref_indexable(obj: object) -> TypeGuard[RefIndexable]:
    """Check if object supports index-based access.

    Args:
        obj: Object to check

    Returns:
        True if object implements RefIndexable protocol
    """
    return isinstance(obj, RefIndexable)


def is_lengthable(obj: object) -> TypeGuard[Lengthable]:
    """Check if object supports length queries.

    Args:
        obj: Object to check

    Returns:
        True if object implements Lengthable protocol
    """
    return isinstance(obj, Lengthable)


def is_mapping_accessible(obj: object) -> TypeGuard[MappingAccessible]:
    """Check if object supports direct mapping access operations.

    Args:
        obj: Object to check

    Returns:
        True if object implements MappingAccessible protocol
    """
    return isinstance(obj, MappingAccessible)
