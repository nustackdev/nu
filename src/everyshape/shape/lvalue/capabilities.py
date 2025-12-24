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

LValues differ from RValues:
- LValues are LOCATIONS in storage (lazy access)
- RValues are ALREADY COMPUTED values in memory

Example:
    >>> if isinstance(ref, Gettable):
    ...     get_op = ref.get()  # Creates GetOp
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeGuard, runtime_checkable


if TYPE_CHECKING:
    from everyshape.shape.term import RValue


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
]


# =============================================================================
# READ CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Gettable[T, OpT](Protocol):
    """Protocol for LValues that support reading a single value.

    Used for primitive value references (ValueRef).
    Returns a GetOp that reads the value when executed.

    Type Parameters:
        T: Type of value at this location
        OpT: Type of the get operation returned

    Example:
        >>> if isinstance(ref, Gettable):
        ...     get_op = ref.get()
        ...     value = get_op.execute(ctx)
    """

    def get(self) -> OpT:
        """Create a get operation for this location.

        Returns:
            GetOp that reads the value when executed
        """
        ...


@runtime_checkable
class Extractable[T, OpT](Protocol):
    """Protocol for LValues that support extracting entire structures.

    Used for container references (ViewRef).
    Returns an ExtractOp that reads the full structure when executed.

    Type Parameters:
        T: Type of extracted value (dict, list, etc.)
        OpT: Type of the extract operation returned

    Example:
        >>> if isinstance(ref, Extractable):
        ...     extract_op = ref.extract()
        ...     data = extract_op.execute(ctx)  # Returns dict/list/etc
    """

    def extract(self) -> OpT:
        """Create an extract operation for this container.

        Returns:
            ExtractOp that extracts entire structure when executed
        """
        ...


# =============================================================================
# WRITE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Settable[T, CmdT](Protocol):
    """Protocol for LValues that support writing a single value.

    Used for primitive value references.
    Returns a SetCmd that writes the value when executed.

    Type Parameters:
        T: Type of value to write
        CmdT: Type of the set command returned

    Example:
        >>> if isinstance(ref, Settable):
        ...     set_cmd = ref.set(new_value)
        ...     set_cmd.execute(ctx)
    """

    def set(self, value: T | RValue) -> CmdT:
        """Create a set command for this location.

        Args:
            value: Value to write (literal or RValue)

        Returns:
            SetCmd that writes the value when executed
        """
        ...


@runtime_checkable
class Storable[T, CmdT](Protocol):
    """Protocol for LValues that support storing entire structures.

    Used for container references.
    Returns a StoreCmd that writes the entire structure when executed.

    Type Parameters:
        T: Type of value to store (dict, list, etc.)
        CmdT: Type of the store command returned

    Example:
        >>> if isinstance(ref, Storable):
        ...     store_cmd = ref.store({"key": "value"})
        ...     store_cmd.execute(ctx)
    """

    def store(self, value: T | RValue) -> CmdT:
        """Create a store command for this container.

        Args:
            value: Value to store (literal or RValue)

        Returns:
            StoreCmd that stores the value when executed
        """
        ...


@runtime_checkable
class Appendable[T, CmdT](Protocol):
    """Protocol for LValues that support appending items.

    Used for sequence references.
    Returns an AppendCmd that appends the item when executed.

    Type Parameters:
        T: Type of item to append
        CmdT: Type of the append command returned

    Example:
        >>> if isinstance(ref, Appendable):
        ...     append_cmd = ref.append(new_item)
        ...     append_cmd.execute(ctx)
    """

    def append(self, value: T | RValue) -> CmdT:
        """Create an append command.

        Args:
            value: Item to append (literal or RValue)

        Returns:
            AppendCmd that appends the item when executed
        """
        ...


@runtime_checkable
class Insertable[T, CmdT](Protocol):
    """Protocol for LValues that support inserting items at index.

    Used for sequence references.
    Returns an InsertCmd that inserts the item when executed.

    Type Parameters:
        T: Type of item to insert
        CmdT: Type of the insert command returned

    Example:
        >>> if isinstance(ref, Insertable):
        ...     insert_cmd = ref.insert(0, new_item)
        ...     insert_cmd.execute(ctx)
    """

    def insert(self, index: int | RValue, value: T | RValue) -> CmdT:
        """Create an insert command.

        Args:
            index: Position to insert at
            value: Item to insert (literal or RValue)

        Returns:
            InsertCmd that inserts the item when executed
        """
        ...


# =============================================================================
# DELETE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Deletable[CmdT](Protocol):
    """Protocol for LValues that support deletion.

    Used for primitive and container item references.
    Returns a DeleteCmd that removes the value when executed.

    Type Parameters:
        CmdT: Type of the delete command returned

    Example:
        >>> if isinstance(ref, Deletable):
        ...     delete_cmd = ref.remove()
        ...     delete_cmd.execute(ctx)
    """

    def remove(self) -> CmdT:
        """Create a delete command for this location.

        Returns:
            DeleteCmd that removes the value when executed
        """
        ...


@runtime_checkable
class Clearable[CmdT](Protocol):
    """Protocol for LValues that support clearing all items.

    Used for container references.
    Returns a ClearCmd that removes all items when executed.

    Type Parameters:
        CmdT: Type of the clear command returned

    Example:
        >>> if isinstance(ref, Clearable):
        ...     clear_cmd = ref.clear()
        ...     clear_cmd.execute(ctx)
    """

    def clear(self) -> CmdT:
        """Create a clear command for this container.

        Returns:
            ClearCmd that clears all items when executed
        """
        ...


@runtime_checkable
class Poppable[T, CmdT](Protocol):
    """Protocol for LValues that support popping items.

    Used for sequence references.
    Returns a PopCmd that removes and returns an item when executed.

    Type Parameters:
        T: Type of item to pop
        CmdT: Type of the pop command returned

    Example:
        >>> if isinstance(ref, Poppable):
        ...     pop_cmd = ref.pop()
        ...     removed = pop_cmd.execute(ctx)
    """

    def pop(self, index: int | RValue = -1) -> CmdT:
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
class Existable[OpT](Protocol):
    """Protocol for LValues that support existence checking.

    Returns operations that check if the location exists.

    Type Parameters:
        OpT: Type of the operation returned

    Example:
        >>> if isinstance(ref, Existable):
        ...     exists_op = ref.exists()
        ...     does_exist = exists_op.execute(ctx)
    """

    def exists(self) -> OpT:
        """Create an existence check operation.

        Returns:
            ExistsOp that returns True if location exists
        """
        ...

    def missing(self) -> OpT:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if location doesn't exist
        """
        ...


# =============================================================================
# OBSERVABLE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class RefObservable[OpT](Protocol):
    """Protocol for LValues that support observing changes.

    Returns operations that create subscriptions to changes.

    Type Parameters:
        OpT: Type of the operation returned

    Example:
        >>> if isinstance(ref, RefObservable):
        ...     change_op = ref.on_change()
        ...     subscription = change_op.execute(ctx)
    """

    def on_change(self) -> OpT:
        """Create a change subscription operation.

        Returns:
            OnChangeOp that creates subscription when executed
        """
        ...


@runtime_checkable
class RefChildObservable[K, OpT](Protocol):
    """Protocol for LValues that support observing child changes.

    Type Parameters:
        K: Type of child address/key
        OpT: Type of the operation returned

    Example:
        >>> if isinstance(ref, RefChildObservable):
        ...     child_op = ref.on_child_change("key")
        ...     subscription = child_op.execute(ctx)
    """

    def on_child_change(self, address: K | RValue) -> OpT:
        """Create a child change subscription operation.

        Args:
            address: Child address to watch

        Returns:
            OnChildChangeOp that creates subscription when executed
        """
        ...

    def on_children_change(self) -> OpT:
        """Create a children change subscription operation.

        Returns:
            OnChildrenChangeOp that creates subscription when executed
        """
        ...


@runtime_checkable
class RefDescendantsObservable[OpT](Protocol):
    """Protocol for LValues that support observing descendant changes.

    Type Parameters:
        OpT: Type of the operation returned

    Example:
        >>> if isinstance(ref, RefDescendantsObservable):
        ...     desc_op = ref.on_descendants_change("*", "status")
        ...     subscription = desc_op.execute(ctx)
    """

    def on_descendants_change(self, *pattern: str | int) -> OpT:
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
class Nestable[K, RefT](Protocol):
    """Protocol for LValues that support navigation to children.

    Used for container references to navigate to nested locations.

    Type Parameters:
        K: Type of child address/key
        RefT: Type of child reference returned

    Example:
        >>> if isinstance(ref, Nestable):
        ...     child_ref = ref["key"]  # Navigate to child
    """

    def __getitem__(self, key: K | RValue) -> RefT:
        """Navigate to child location.

        Args:
            key: Child address/key

        Returns:
            Reference to child location
        """
        ...


@runtime_checkable
class RefIndexable[K, RefT](Protocol):
    """Protocol for LValues that support index-based access.

    Type Parameters:
        K: Type of index (typically int)
        RefT: Type of item reference returned

    Example:
        >>> if isinstance(ref, RefIndexable):
        ...     item_ref = ref[0]  # Get first item reference
    """

    def __getitem__(self, key: K | RValue) -> RefT:
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
class Lengthable[OpT](Protocol):
    """Protocol for LValues that support length queries.

    Type Parameters:
        OpT: Type of the length operation returned

    Example:
        >>> if isinstance(ref, Lengthable):
        ...     len_op = ref.length()
        ...     size = len_op.execute(ctx)
    """

    def length(self) -> OpT:
        """Create a length query operation.

        Returns:
            LengthOp that returns the length when executed
        """
        ...


@runtime_checkable
class KeysQueryable[OpT](Protocol):
    """Protocol for LValues that support keys queries.

    Type Parameters:
        OpT: Type of the keys operation returned

    Example:
        >>> if isinstance(ref, KeysQueryable):
        ...     keys_op = ref.keys()
        ...     all_keys = keys_op.execute(ctx)
    """

    def keys(self) -> OpT:
        """Create a keys query operation.

        Returns:
            KeysOp that returns all keys when executed
        """
        ...


@runtime_checkable
class ValuesQueryable[OpT](Protocol):
    """Protocol for LValues that support values queries.

    Type Parameters:
        OpT: Type of the values operation returned

    Example:
        >>> if isinstance(ref, ValuesQueryable):
        ...     values_op = ref.values()
        ...     all_values = values_op.execute(ctx)
    """

    def values(self) -> OpT:
        """Create a values query operation.

        Returns:
            ValuesOp that returns all values when executed
        """
        ...


@runtime_checkable
class ItemsQueryable[OpT](Protocol):
    """Protocol for LValues that support items queries.

    Type Parameters:
        OpT: Type of the items operation returned

    Example:
        >>> if isinstance(ref, ItemsQueryable):
        ...     items_op = ref.items()
        ...     all_items = items_op.execute(ctx)
    """

    def items(self) -> OpT:
        """Create an items query operation.

        Returns:
            ItemsOp that returns all (key, value) pairs when executed
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
