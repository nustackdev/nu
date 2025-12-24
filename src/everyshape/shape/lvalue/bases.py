"""Reusable behavior bases for LValue implementations.

This module provides mixin classes that encapsulate common LValue patterns:
- GettableBase: Get operations for primitive refs
- SettableBase: Set operations for primitive refs
- ExtractableBase: Extract operations for view refs
- StorableBase: Store operations for view refs
- ObservableBase: Change observation operations
- SequenceOpsBase: Sequence-specific operations
- MappingOpsBase: Mapping-specific operations

These bases use composition to build complete LValue types.
"""

from __future__ import annotations

from abc import abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyshape.shape.term import RValue


__all__ = [
    "ChildObservableBase",
    "ClearableBase",
    "DeletableBase",
    "ExistableBase",
    "ExtractableBase",
    "GettableBase",
    "LengthableBase",
    "MappingOpsBase",
    "ObservableBase",
    "SequenceOpsBase",
    "SettableBase",
    "StorableBase",
]


logger = getLogger(__name__)


# =============================================================================
# PRIMITIVE REF BASES
# =============================================================================


class GettableBase[T, OpT]:
    """Base for LValues that support get operations.

    Provides get() method that creates a GetOp.

    Type Parameters:
        T: Type of value at this location
        OpT: Type of GetOp to return

    Example:
        >>> class ValueRef(GettableBase[int, GetOp]):
        ...     pass
        >>> ref = ValueRef(...)
        >>> get_op = ref.get()  # Creates GetOp
    """

    @abstractmethod
    def get(self) -> OpT:
        """Create a get operation.

        Returns:
            GetOp that reads the value when executed
        """
        ...


class SettableBase[T, CmdT]:
    """Base for LValues that support set operations.

    Provides set() method that creates a SetCmd.

    Type Parameters:
        T: Type of value to write
        CmdT: Type of SetCmd to return

    Example:
        >>> class ValueRef(SettableBase[int, SetCmd]):
        ...     pass
        >>> ref = ValueRef(...)
        >>> set_cmd = ref.set(42)  # Creates SetCmd
    """

    @abstractmethod
    def set(self, value: T | RValue) -> CmdT:
        """Create a set command.

        Args:
            value: Value to write (literal or RValue)

        Returns:
            SetCmd that writes the value when executed
        """
        ...


class DeletableBase[CmdT]:
    """Base for LValues that support delete operations.

    Provides remove() method that creates a DeleteCmd.

    Type Parameters:
        CmdT: Type of DeleteCmd to return

    Example:
        >>> class ValueRef(DeletableBase[DeleteCmd]):
        ...     pass
        >>> ref = ValueRef(...)
        >>> delete_cmd = ref.remove()  # Creates DeleteCmd
    """

    @abstractmethod
    def remove(self) -> CmdT:
        """Create a delete command.

        Returns:
            DeleteCmd that removes the value when executed
        """
        ...


# =============================================================================
# VIEW REF BASES
# =============================================================================


class ExtractableBase[T, OpT]:
    """Base for LValues that support extract operations.

    Provides extract() method that creates an ExtractOp.

    Type Parameters:
        T: Type of extracted value (dict, list, etc.)
        OpT: Type of ExtractOp to return

    Example:
        >>> class DictRef(ExtractableBase[dict, ExtractOp]):
        ...     pass
        >>> ref = DictRef(...)
        >>> extract_op = ref.extract()  # Creates ExtractOp
    """

    @abstractmethod
    def extract(self) -> OpT:
        """Create an extract operation.

        Returns:
            ExtractOp that extracts the structure when executed
        """
        ...


class StorableBase[T, CmdT]:
    """Base for LValues that support store operations.

    Provides store() method that creates a StoreCmd.

    Type Parameters:
        T: Type of value to store
        CmdT: Type of StoreCmd to return

    Example:
        >>> class DictRef(StorableBase[dict, StoreCmd]):
        ...     pass
        >>> ref = DictRef(...)
        >>> store_cmd = ref.store({"key": "value"})  # Creates StoreCmd
    """

    @abstractmethod
    def store(self, value: T | RValue) -> CmdT:
        """Create a store command.

        Args:
            value: Value to store (literal or RValue)

        Returns:
            StoreCmd that stores the value when executed
        """
        ...


class ClearableBase[CmdT]:
    """Base for LValues that support clear operations.

    Provides clear() method that creates a ClearCmd.

    Type Parameters:
        CmdT: Type of ClearCmd to return

    Example:
        >>> class DictRef(ClearableBase[ClearCmd]):
        ...     pass
        >>> ref = DictRef(...)
        >>> clear_cmd = ref.clear()  # Creates ClearCmd
    """

    @abstractmethod
    def clear(self) -> CmdT:
        """Create a clear command.

        Returns:
            ClearCmd that clears all items when executed
        """
        ...


# =============================================================================
# EXISTENCE BASES
# =============================================================================


class ExistableBase[OpT]:
    """Base for LValues that support existence checking.

    Provides exists() and missing() methods.

    Type Parameters:
        OpT: Type of operations to return

    Example:
        >>> class ValueRef(ExistableBase[ExistsOp]):
        ...     pass
        >>> ref = ValueRef(...)
        >>> exists_op = ref.exists()  # Creates ExistsOp
    """

    @abstractmethod
    def exists(self) -> OpT:
        """Create an existence check operation.

        Returns:
            ExistsOp that returns True if location exists
        """
        ...

    @abstractmethod
    def missing(self) -> OpT:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if location doesn't exist
        """
        ...


# =============================================================================
# OBSERVABLE BASES
# =============================================================================


class ObservableBase[OpT]:
    """Base for LValues that support change observation.

    Provides on_change() method that creates an OnChangeOp.

    Type Parameters:
        OpT: Type of OnChangeOp to return

    Example:
        >>> class DictRef(ObservableBase[OnChangeOp]):
        ...     pass
        >>> ref = DictRef(...)
        >>> change_op = ref.on_change()  # Creates OnChangeOp
    """

    @abstractmethod
    def on_change(self) -> OpT:
        """Create a change subscription operation.

        Returns:
            OnChangeOp that creates subscription when executed
        """
        ...


class ChildObservableBase[K, OpT]:
    """Base for LValues that support child change observation.

    Provides on_child_change() and on_children_change() methods.

    Type Parameters:
        K: Type of child address/key
        OpT: Type of operations to return

    Example:
        >>> class DictRef(ChildObservableBase[str, OnChildChangeOp]):
        ...     pass
        >>> ref = DictRef(...)
        >>> child_op = ref.on_child_change("key")
    """

    @abstractmethod
    def on_child_change(self, address: K | RValue) -> OpT:
        """Create a child change subscription operation.

        Args:
            address: Child address to watch

        Returns:
            OnChildChangeOp that creates subscription when executed
        """
        ...

    @abstractmethod
    def on_children_change(self) -> OpT:
        """Create a children change subscription operation.

        Returns:
            OnChildrenChangeOp that creates subscription when executed
        """
        ...


# =============================================================================
# QUERY BASES
# =============================================================================


class LengthableBase[OpT]:
    """Base for LValues that support length queries.

    Provides length() method that creates a LengthOp.

    Type Parameters:
        OpT: Type of LengthOp to return

    Example:
        >>> class ListRef(LengthableBase[LengthOp]):
        ...     pass
        >>> ref = ListRef(...)
        >>> len_op = ref.length()  # Creates LengthOp
    """

    @abstractmethod
    def length(self) -> OpT:
        """Create a length query operation.

        Returns:
            LengthOp that returns length when executed
        """
        ...


# =============================================================================
# SEQUENCE OPERATION BASES
# =============================================================================


class SequenceOpsBase[T, RefT, OpT, CmdT]:
    """Base for LValues with sequence operations.

    Provides sequence-specific operations like append, pop,
    map, filter, reduce.

    Type Parameters:
        T: Type of items in the sequence
        RefT: Type of item references
        OpT: Type of operations to return
        CmdT: Type of commands to return

    Example:
        >>> class ListRef(SequenceOpsBase[int, ValueRef, MapOp, AppendCmd]):
        ...     pass
        >>> ref = ListRef(...)
        >>> append_cmd = ref.append(42)
        >>> map_op = ref.map(lambda x: x * 2)
    """

    @abstractmethod
    def __getitem__(self, key: int | slice | RValue) -> RefT:
        """Get item or slice reference.

        Args:
            key: Index or slice

        Returns:
            Reference to item or slice
        """
        ...

    @abstractmethod
    def append(self, value: T | RValue) -> CmdT:
        """Create an append command.

        Args:
            value: Item to append

        Returns:
            AppendCmd that appends the item when executed
        """
        ...

    def map[R](self, func: object) -> OpT:
        """Create a map operation.

        Args:
            func: Function to apply to each element

        Returns:
            MapOp that maps when executed
        """
        ...

    def filter(self, predicate: object) -> OpT:
        """Create a filter operation.

        Args:
            predicate: Filter function

        Returns:
            FilterOp that filters when executed
        """
        ...

    def reduce[R](self, func: object, initial: R | RValue) -> OpT:
        """Create a reduce operation.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            ReduceOp that reduces when executed
        """
        ...


# =============================================================================
# MAPPING OPERATION BASES
# =============================================================================


class MappingOpsBase[K, V, RefT, OpT, CmdT]:
    """Base for LValues with mapping operations.

    Provides mapping-specific operations like keys, values, items,
    map_values, filter.

    Type Parameters:
        K: Type of keys
        V: Type of values
        RefT: Type of item references
        OpT: Type of operations to return
        CmdT: Type of commands to return

    Example:
        >>> class DictRef(MappingOpsBase[str, int, ValueRef, KeysOp, StoreCmd]):
        ...     pass
        >>> ref = DictRef(...)
        >>> keys_op = ref.keys()
        >>> values_op = ref.values()
    """

    @abstractmethod
    def __getitem__(self, key: K | RValue) -> RefT:
        """Get item reference by key.

        Args:
            key: Key value

        Returns:
            Reference to item at key
        """
        ...

    @abstractmethod
    def keys(self) -> OpT:
        """Create a keys query operation.

        Returns:
            KeysOp that returns keys when executed
        """
        ...

    @abstractmethod
    def values(self) -> OpT:
        """Create a values query operation.

        Returns:
            ValuesOp that returns values when executed
        """
        ...

    @abstractmethod
    def items(self) -> OpT:
        """Create an items query operation.

        Returns:
            ItemsOp that returns items when executed
        """
        ...

    def map_values[R](self, func: object) -> OpT:
        """Create a map_values operation.

        Args:
            func: Function to apply to each value

        Returns:
            MapValuesOp that maps when executed
        """
        ...

    def filter(self, predicate: object) -> OpT:
        """Create a filter operation.

        Args:
            predicate: Filter function (key, value) -> bool

        Returns:
            FilterItemsOp that filters when executed
        """
        ...
