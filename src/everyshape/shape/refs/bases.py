"""Comprehensive behavior bases for LValue implementations.

This module provides mixin classes that encapsulate LValue behaviors.
Each base provides concrete methods that create operations/commands directly.

Hierarchy:
    PrimitiveRefBase - leaf value references
        Methods: get(), set(), remove(), exists(), missing()

    ViewRefBase - container references
        Methods: extract(), store(), clear(), length(), exists(), missing()

    SequenceRefBase(ViewRefBase) - list-like containers
        Adds: __getitem__ (int/slice), map(), filter(), reduce(), find(), etc.

    MutableSequenceRefBase(SequenceRefBase) - mutable lists
        Adds: append(), insert(), pop()

    MappingRefBase(ViewRefBase) - dict-like containers
        Adds: __getitem__ (key), keys(), values(), items(), map_values(), filter(), etc.

    SetRefBase(ViewRefBase) - set-like containers

    MutableSetRefBase(SetRefBase) - mutable sets
        Adds: add(), remove(), discard()

Usage:
    class MyValueRef(PrimitiveRefBase[int, MyContext]):
        # Just inherit - all methods work automatically
        pass

    >>> ref = MyValueRef(...)
    >>> get_op = ref.get()  # Returns GetOp
    >>> set_cmd = ref.set(42)  # Returns SetCmd
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everyshape.shape.context import ContextProtocol
from everyshape.shape.term import PrimitiveRef, RValue, ViewRef
from everyshape.shape.values.conversion import literal
from everyshape.types import SpecialValue, Value

from .commands import (
    AddCmd,
    AppendCmd,
    ClearCmd,
    DeleteCmd,
    DiscardCmd,
    InsertCmd,
    PopCmd,
    RemoveCmd,
    SetCmd,
    StoreCmd,
)
from .operations import (
    CountOp,
    ExistsOp,
    ExtractOp,
    FilterItemsOp,
    FilterOp,
    FindIndexOp,
    FindItemOp,
    FindKeyOp,
    FindOp,
    FindValueOp,
    GetOp,
    IndexOp,
    ItemsOp,
    KeysOp,
    LengthOp,
    MapItemsOp,
    MapOp,
    MapValuesOp,
    MissingOp,
    ReduceItemsOp,
    ReduceOp,
    ValuesOp,
)


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "MappingRefBase",
    "MutableMappingRefBase",
    "MutableSequenceRefBase",
    "MutableSetRefBase",
    "PrimitiveRefBase",
    "SequenceRefBase",
    "SetRefBase",
    "ViewRefBase",
]


# =============================================================================
# PRIMITIVE REF BASE
# =============================================================================


class PrimitiveRefBase[T: Value, ContextT: ContextProtocol](PrimitiveRef[T, ContextT]):
    """Complete base for primitive (leaf) value references.

    Provides all standard operations for primitive values:
    - get() -> GetOp (read value)
    - set(value) -> SetCmd (write value)
    - remove() -> DeleteCmd (delete value)
    - exists() -> ExistsOp (check existence)
    - missing() -> MissingOp (check non-existence)

    Type Parameters:
        T: Type of value at this location
        ContextT: Execution context type

    Example:
        >>> class ValueRef(PrimitiveRefBase[int, Context]):
        ...     pass
        >>> ref = ValueRef(...)
        >>> get_op = ref.get()  # Creates GetOp
        >>> set_cmd = ref.set(42)  # Creates SetCmd
    """

    def _wrap_value(
        self, value: T | RValue[T | SpecialValue, ContextT]
    ) -> RValue[T | SpecialValue, ContextT]:
        """Wrap a raw value in a Literal if needed.

        Args:
            value: Raw value or RValue

        Returns:
            RValue wrapping the value
        """
        if isinstance(value, RValue):
            return value
        return literal(value)

    def get(self) -> GetOp[T, ContextT]:
        """Create a get operation for this location.

        Returns:
            GetOp that reads the value when executed

        Example:
            >>> value = ref.get().execute(ctx)
        """
        return GetOp(self)

    def set(self, value: T | RValue[T | SpecialValue, ContextT]) -> SetCmd[T, ContextT]:
        """Create a set command for this location.

        Args:
            value: Value to write (literal or RValue)

        Returns:
            SetCmd that writes the value when executed

        Example:
            >>> ref.set(42).execute(ctx)
            >>> ref.set(other_ref.get()).execute(ctx)  # Chain refs
        """
        return SetCmd(self, self._wrap_value(value))

    def remove(self) -> DeleteCmd[ContextT]:
        """Create a delete command for this location.

        Returns:
            DeleteCmd that removes the value when executed

        Example:
            >>> ref.remove().execute(ctx)
        """
        return DeleteCmd(self)

    def exists(self) -> ExistsOp[ContextT]:
        """Create an existence check operation.

        Returns:
            ExistsOp that returns True if location exists

        Example:
            >>> if ref.exists().execute(ctx):
            ...     print("Value exists")
        """
        return ExistsOp(self)

    def missing(self) -> MissingOp[ContextT]:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if location doesn't exist

        Example:
            >>> if ref.missing().execute(ctx):
            ...     ref.set(default_value).execute(ctx)
        """
        return MissingOp(self)


# =============================================================================
# VIEW REF BASE
# =============================================================================


class ViewRefBase[T: Value, ContextT: ContextProtocol](ViewRef[object, ContextT]):
    """Complete base for container (view) references.

    Provides all standard operations for containers:
    - extract() -> ExtractOp (read entire structure)
    - store(value) -> StoreCmd (write entire structure)
    - clear() -> ClearCmd (remove all items)
    - length() -> LengthOp (query size)
    - exists() -> ExistsOp (check existence)
    - missing() -> MissingOp (check non-existence)

    Type Parameters:
        T: Type of extracted value (dict, list, etc.)
        ContextT: Execution context type
    """

    def _wrap_value(
        self, value: T | RValue[T | SpecialValue, ContextT]
    ) -> RValue[T | SpecialValue, ContextT]:
        """Wrap a raw value in a Literal if needed."""
        if isinstance(value, RValue):
            return value
        return literal(value)

    def extract(self) -> ExtractOp[T, ContextT]:
        """Create an extract operation for this container.

        Returns:
            ExtractOp that extracts entire structure when executed

        Example:
            >>> data = dict_ref.extract().execute(ctx)  # Returns dict
        """
        return ExtractOp(self)

    def store(self, value: T | RValue[T | SpecialValue, ContextT]) -> StoreCmd[T, ContextT]:
        """Create a store command for this container.

        Args:
            value: Value to store (literal or RValue)

        Returns:
            StoreCmd that stores the value when executed

        Example:
            >>> dict_ref.store({"key": "value"}).execute(ctx)
        """
        return StoreCmd(self, self._wrap_value(value))

    def clear(self) -> ClearCmd[ContextT]:
        """Create a clear command for this container.

        Returns:
            ClearCmd that clears all items when executed

        Example:
            >>> list_ref.clear().execute(ctx)
        """
        return ClearCmd(self)

    def length(self) -> LengthOp[ContextT]:
        """Create a length query operation.

        Returns:
            LengthOp that returns length when executed

        Example:
            >>> count = list_ref.length().execute(ctx)
        """
        return LengthOp(self)

    def exists(self) -> ExistsOp[ContextT]:
        """Create an existence check operation.

        Returns:
            ExistsOp that returns True if container exists
        """
        return ExistsOp(self)

    def missing(self) -> MissingOp[ContextT]:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if container doesn't exist
        """
        return MissingOp(self)


# =============================================================================
# SEQUENCE REF BASE
# =============================================================================


class SequenceRefBase[T: Value, ItemRefT, SliceRefT, ContextT: ContextProtocol](
    ViewRefBase[list[T], ContextT]
):
    """Complete base for read-only sequence references.

    Extends ViewRefBase with sequence capabilities:
    - __getitem__(int) -> item reference
    - __getitem__(slice) -> slice reference
    - map(func) -> MapOp
    - filter(predicate) -> FilterOp
    - reduce(func, initial) -> ReduceOp
    - find(predicate) -> FindOp
    - find_index(predicate) -> FindIndexOp
    - index(value) -> IndexOp
    - count(value) -> CountOp

    Type Parameters:
        T: Type of items in the sequence
        ItemRefT: Type of reference returned for single items
        SliceRefT: Type of reference returned for slices
        ContextT: Execution context type
    """

    def _create_item_ref(self, index: int | RValue[int, ContextT]) -> ItemRefT:
        """Create a reference to an item. Override in subclass.

        Args:
            index: Item index

        Returns:
            Reference to item at index
        """
        raise NotImplementedError("Subclass must implement _create_item_ref")

    def _create_slice_ref(self, key: slice) -> SliceRefT:
        """Create a reference to a slice. Override in subclass.

        Args:
            key: Slice specification

        Returns:
            Reference to slice
        """
        raise NotImplementedError("Subclass must implement _create_slice_ref")

    @overload
    def __getitem__(self, key: int) -> ItemRefT: ...

    @overload
    def __getitem__(self, key: slice) -> SliceRefT: ...

    @overload
    def __getitem__(self, key: RValue[int, ContextT]) -> ItemRefT: ...

    def __getitem__(self, key: int | slice | RValue[int, ContextT]) -> ItemRefT | SliceRefT:
        """Get item or slice reference.

        Args:
            key: Index (int/RValue) or slice

        Returns:
            Reference to item or slice

        Example:
            >>> item_ref = list_ref[0]
            >>> slice_ref = list_ref[1:3]
        """
        if isinstance(key, slice):
            return self._create_slice_ref(key)
        return self._create_item_ref(key)

    def map[R: Value](self, func: Callable[[T], R]) -> MapOp[T, R, ContextT]:
        """Map a function over sequence elements.

        Args:
            func: Function to apply to each element

        Returns:
            MapOp that applies func at execution time

        Example:
            >>> doubled = list_ref.map(lambda x: x * 2).execute(ctx)
        """
        return MapOp(self, func)

    def filter(self, predicate: Callable[[T], bool]) -> FilterOp[T, ContextT]:
        """Filter sequence elements by predicate.

        Args:
            predicate: Function returning True for elements to keep

        Returns:
            FilterOp that filters at execution time

        Example:
            >>> evens = list_ref.filter(lambda x: x % 2 == 0).execute(ctx)
        """
        return FilterOp(self, predicate)

    def reduce[R](self, func: Callable[[R, T], R], initial: R) -> ReduceOp[T, R, ContextT]:
        """Reduce sequence to single value.

        Args:
            func: Function (accumulator, element) -> accumulator
            initial: Starting value for accumulator

        Returns:
            ReduceOp that reduces at execution time

        Example:
            >>> total = list_ref.reduce(lambda acc, x: acc + x, 0).execute(ctx)
        """
        return ReduceOp(self, func, initial)

    def find(self, predicate: Callable[[T], bool]) -> FindOp[T, ContextT]:
        """Find first element matching predicate.

        Args:
            predicate: Function returning True for element to find

        Returns:
            FindOp that returns element at execution time

        Example:
            >>> first_even = list_ref.find(lambda x: x % 2 == 0).execute(ctx)
        """
        return FindOp(self, predicate)

    def find_index(self, predicate: Callable[[T], bool]) -> FindIndexOp[T, ContextT]:
        """Find index of first element matching predicate.

        Args:
            predicate: Function returning True for element to find

        Returns:
            FindIndexOp that returns index at execution time

        Example:
            >>> idx = list_ref.find_index(lambda x: x > 10).execute(ctx)
        """
        return FindIndexOp(self, predicate)

    def index(self, value: T) -> IndexOp[T, ContextT]:
        """Find index of value in sequence.

        Args:
            value: Value to search for

        Returns:
            IndexOp that returns index at execution time

        Example:
            >>> idx = list_ref.index("apple").execute(ctx)
        """
        return IndexOp(self, value)

    def count(self, value: T) -> CountOp[T, ContextT]:
        """Count occurrences of value in sequence.

        Args:
            value: Value to count

        Returns:
            CountOp that returns count at execution time

        Example:
            >>> n = list_ref.count("apple").execute(ctx)
        """
        return CountOp(self, value)


class MutableSequenceRefBase[T: Value, ItemRefT, SliceRefT, ContextT: ContextProtocol](
    SequenceRefBase[T, ItemRefT, SliceRefT, ContextT]
):
    """Complete base for mutable sequence references.

    Extends SequenceRefBase with mutation capabilities:
    - append(value) -> AppendCmd
    - insert(index, value) -> InsertCmd
    - pop(index?) -> PopCmd

    Type Parameters:
        T: Type of items in the sequence
        ItemRefT: Type of reference returned for single items
        SliceRefT: Type of reference returned for slices
        ContextT: Execution context type
    """

    def _wrap_index(
        self, index: int | RValue[int | SpecialValue, ContextT]
    ) -> RValue[int | SpecialValue, ContextT]:
        """Wrap an index in a Literal if needed."""
        if isinstance(index, RValue):
            return index
        return literal(index)

    def append(self, value: T | RValue[T | SpecialValue, ContextT]) -> AppendCmd[T, ContextT]:
        """Create an append command.

        Args:
            value: Item to append (literal or RValue)

        Returns:
            AppendCmd that appends the item when executed

        Example:
            >>> list_ref.append(42).execute(ctx)
        """
        return AppendCmd(self, self._wrap_value(value))

    def insert(
        self,
        index: int | RValue[int | SpecialValue, ContextT],
        value: T | RValue[T | SpecialValue, ContextT],
    ) -> InsertCmd[T, ContextT]:
        """Create an insert command.

        Args:
            index: Position to insert at
            value: Item to insert (literal or RValue)

        Returns:
            InsertCmd that inserts the item when executed

        Example:
            >>> list_ref.insert(0, "first").execute(ctx)
        """
        return InsertCmd(self, self._wrap_index(index), self._wrap_value(value))

    def pop(
        self, index: int | RValue[int | SpecialValue, ContextT] | None = None
    ) -> PopCmd[T, ContextT]:
        """Create a pop command.

        Args:
            index: Position to pop from (default: last)

        Returns:
            PopCmd that removes and returns the item when executed

        Example:
            >>> last = list_ref.pop().execute(ctx)
            >>> first = list_ref.pop(0).execute(ctx)
        """
        wrapped_index = self._wrap_index(index) if index is not None else None
        return PopCmd(self, wrapped_index)


# =============================================================================
# MAPPING REF BASE
# =============================================================================


class MappingRefBase[K, V: Value, ChildRefT, ContextT: ContextProtocol](
    ViewRefBase[dict[K, V], ContextT]
):
    """Complete base for read-only mapping references.

    Extends ViewRefBase with mapping capabilities:
    - __getitem__(key) -> child reference
    - keys() -> KeysOp
    - values() -> ValuesOp
    - items() -> ItemsOp
    - map_values(func) -> MapValuesOp
    - map_items(func) -> MapItemsOp
    - filter(predicate) -> FilterItemsOp
    - reduce(func, initial) -> ReduceItemsOp
    - find_key(predicate) -> FindKeyOp
    - find_value(predicate) -> FindValueOp
    - find_item(predicate) -> FindItemOp

    Type Parameters:
        K: Type of keys
        V: Type of values
        ChildRefT: Type of reference returned for child items
        ContextT: Execution context type
    """

    def _create_child_ref(self, key: K | RValue[K, ContextT]) -> ChildRefT:
        """Create a reference to a child. Override in subclass.

        Args:
            key: Child key

        Returns:
            Reference to child at key
        """
        raise NotImplementedError("Subclass must implement _create_child_ref")

    def __getitem__(self, key: K | RValue[K, ContextT]) -> ChildRefT:
        """Get child reference by key.

        Args:
            key: Key value

        Returns:
            Reference to item at key

        Example:
            >>> user_ref = users_ref["alice"]
        """
        return self._create_child_ref(key)

    def keys(self) -> KeysOp[K, ContextT]:
        """Create a keys query operation.

        Returns:
            KeysOp that returns all keys when executed

        Example:
            >>> all_keys = dict_ref.keys().execute(ctx)
        """
        return KeysOp(self)

    def values(self) -> ValuesOp[V, ContextT]:
        """Create a values query operation.

        Returns:
            ValuesOp that returns all values when executed

        Example:
            >>> all_values = dict_ref.values().execute(ctx)
        """
        return ValuesOp(self)

    def items(self) -> ItemsOp[K, V, ContextT]:
        """Create an items query operation.

        Returns:
            ItemsOp that returns all (key, value) pairs when executed

        Example:
            >>> all_items = dict_ref.items().execute(ctx)
        """
        return ItemsOp(self)

    def map_values[R: Value](self, func: Callable[[V], R]) -> MapValuesOp[K, V, R, ContextT]:
        """Map function over mapping values.

        Args:
            func: Function to apply to each value

        Returns:
            MapValuesOp that returns transformed dict at execution time

        Example:
            >>> doubled = scores_ref.map_values(lambda x: x * 2).execute(ctx)
        """
        return MapValuesOp(self, func)

    def map_items[K2, V2: Value](
        self, func: Callable[[K, V], tuple[K2, V2]]
    ) -> MapItemsOp[K, V, K2, V2, ContextT]:
        """Map function over mapping items.

        Args:
            func: Function (key, value) -> (new_key, new_value)

        Returns:
            MapItemsOp that returns transformed dict at execution time

        Example:
            >>> upper_keys = dict_ref.map_items(lambda k, v: (k.upper(), v)).execute(ctx)
        """
        return MapItemsOp(self, func)

    def filter(self, predicate: Callable[[K, V], bool]) -> FilterItemsOp[K, V, ContextT]:
        """Filter mapping items by predicate.

        Args:
            predicate: Function (key, value) -> bool, keep if True

        Returns:
            FilterItemsOp that returns filtered dict at execution time

        Example:
            >>> high_scores = scores_ref.filter(lambda k, v: v > 100).execute(ctx)
        """
        return FilterItemsOp(self, predicate)

    def reduce[R](
        self, func: Callable[[R, K, V], R], initial: R
    ) -> ReduceItemsOp[K, V, R, ContextT]:
        """Reduce mapping to single value.

        Args:
            func: Function (accumulator, key, value) -> new_accumulator
            initial: Starting value for accumulator

        Returns:
            ReduceItemsOp that returns reduced value at execution time

        Example:
            >>> total = scores_ref.reduce(lambda acc, k, v: acc + v, 0).execute(ctx)
        """
        return ReduceItemsOp(self, func, initial)

    def find_key(self, predicate: Callable[[V], bool]) -> FindKeyOp[K, V, ContextT]:
        """Find first key whose value matches predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            FindKeyOp that returns matching key at execution time

        Example:
            >>> winner = scores_ref.find_key(lambda v: v >= 100).execute(ctx)
        """
        return FindKeyOp(self, predicate)

    def find_value(self, predicate: Callable[[V], bool]) -> FindValueOp[K, V, ContextT]:
        """Find first value matching predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            FindValueOp that returns matching value at execution time

        Example:
            >>> high_score = scores_ref.find_value(lambda v: v >= 100).execute(ctx)
        """
        return FindValueOp(self, predicate)

    def find_item(self, predicate: Callable[[K, V], bool]) -> FindItemOp[K, V, ContextT]:
        """Find first item (key, value) matching predicate.

        Args:
            predicate: Function (key, value) -> bool

        Returns:
            FindItemOp that returns matching (key, value) tuple at execution time

        Example:
            >>> item = dict_ref.find_item(lambda k, v: k.startswith("admin")).execute(ctx)
        """
        return FindItemOp(self, predicate)


class MutableMappingRefBase[K, V: Value, ChildRefT, ContextT: ContextProtocol](
    MappingRefBase[K, V, ChildRefT, ContextT]
):
    """Complete base for mutable mapping references.

    Same as MappingRefBase - mutations happen through child refs.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ChildRefT: Type of reference returned for child items
        ContextT: Execution context type
    """

    pass


# =============================================================================
# SET REF BASE
# =============================================================================


class SetRefBase[T: Value, ContextT: ContextProtocol](ViewRefBase[set[T], ContextT]):
    """Complete base for read-only set references.

    Extends ViewRefBase for set semantics.

    Type Parameters:
        T: Type of items in the set
        ContextT: Execution context type
    """

    pass


class MutableSetRefBase[T: Value, ContextT: ContextProtocol](SetRefBase[T, ContextT]):
    """Complete base for mutable set references.

    Extends SetRefBase with mutation capabilities:
    - add(value) -> AddCmd
    - remove(value) -> RemoveCmd (raises error if missing)
    - discard(value) -> DiscardCmd (no error if missing)

    Type Parameters:
        T: Type of items in the set
        ContextT: Execution context type
    """

    def add(self, value: T | RValue[T | SpecialValue, ContextT]) -> AddCmd[T, ContextT]:
        """Create an add command.

        Args:
            value: Item to add (literal or RValue)

        Returns:
            AddCmd that adds the item when executed

        Example:
            >>> set_ref.add("item").execute(ctx)
        """
        return AddCmd(self, self._wrap_value(value))

    def remove(self, value: T | RValue[T | SpecialValue, ContextT]) -> RemoveCmd[T, ContextT]:
        """Create a remove command.

        Args:
            value: Item to remove (literal or RValue)

        Returns:
            RemoveCmd that removes the item when executed

        Note:
            Raises KeyError at execution if item not found.

        Example:
            >>> set_ref.remove("item").execute(ctx)
        """
        return RemoveCmd(self, self._wrap_value(value))

    def discard(self, value: T | RValue[T | SpecialValue, ContextT]) -> DiscardCmd[T, ContextT]:
        """Create a discard command.

        Args:
            value: Item to discard (literal or RValue)

        Returns:
            DiscardCmd that discards the item when executed (no error if missing)

        Example:
            >>> set_ref.discard("item").execute(ctx)  # No error if missing
        """
        return DiscardCmd(self, self._wrap_value(value))
