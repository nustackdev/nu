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

from abc import ABC, abstractmethod
from collections.abc import Callable
from collections.abc import Mapping as PyMapping
from collections.abc import Sequence as PySequence
from collections.abc import Set as PySet
from typing import TYPE_CHECKING, overload

from everyshape.types import SpecialValue, Value

from ..term import PrimitiveRef, RValue, ViewRef
from ..values import (
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    ListValue,
    NoneValue,
    SetValue,
    StrValue,
    TupleValue,
)
from ..values.conversion import literal, result
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
from .operations_reactive import (
    OnChangeOp,
    OnChildChangeOp,
    OnChildrenChangeOp,
    OnDescendantsChangeOp,
    OnPrimitiveChangeOp,
)


if TYPE_CHECKING:
    from everyshape.loc import key


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


class PrimitiveRefBase[T: Value](PrimitiveRef[T]):
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

    # Primitives
    @overload
    def get(self: PrimitiveRefBase[int]) -> IntValue: ...

    @overload
    def get(self: PrimitiveRefBase[str]) -> StrValue: ...

    @overload
    def get(self: PrimitiveRefBase[bool]) -> BoolValue: ...

    @overload
    def get(self: PrimitiveRefBase[float]) -> FloatValue: ...

    @overload
    def get(self: PrimitiveRefBase[bytes]) -> BytesValue: ...

    @overload
    def get(self: PrimitiveRefBase[None]) -> NoneValue: ...

    # Collections
    @overload
    def get[V](self: PrimitiveRefBase[list[V]]) -> ListValue[V]: ...

    @overload
    def get[K, V](self: PrimitiveRefBase[dict[K, V]]) -> DictValue[K, V]: ...

    @overload
    def get[V](self: PrimitiveRefBase[set[V]]) -> SetValue[V]: ...

    # @overload
    # def get[*Ts](self: ValueRef[tuple[*Ts]]) -> TupleValue[*Ts, Context]: ...

    # @overload
    # def get[V](self: ValueRef[frozenset[V]]) -> FrozenSetValue[V, Context]: ...

    def get(self) -> object:
        """Create a get operation for this location.

        Returns:
            GetOp that reads the value when executed

        Example:
            >>> value = ref.get().execute(ctx)
        """
        return result(self.value_type, GetOp(self))

    @overload
    def set(self: PrimitiveRefBase[int], value: T | RValue[T | SpecialValue]) -> IntValue: ...

    @overload
    def set(self: PrimitiveRefBase[str], value: T | RValue[T | SpecialValue]) -> StrValue: ...

    @overload
    def set(self: PrimitiveRefBase[bool], value: T | RValue[T | SpecialValue]) -> BoolValue: ...

    @overload
    def set(self: PrimitiveRefBase[float], value: T | RValue[T | SpecialValue]) -> FloatValue: ...

    @overload
    def set(self: PrimitiveRefBase[bytes], value: T | RValue[T | SpecialValue]) -> BytesValue: ...

    @overload
    def set(self: PrimitiveRefBase[None], value: T | RValue[T | SpecialValue]) -> NoneValue: ...

    # Collections
    @overload
    def set[V](
        self: PrimitiveRefBase[list[V]], value: T | RValue[T | SpecialValue]
    ) -> ListValue[V]: ...

    @overload
    def set[K, V](
        self: PrimitiveRefBase[dict[K, V]], value: T | RValue[T | SpecialValue]
    ) -> DictValue[K, V]: ...

    @overload
    def set[V](
        self: PrimitiveRefBase[set[V]], value: T | RValue[T | SpecialValue]
    ) -> SetValue[V]: ...

    def set(self, value: T | RValue[T | SpecialValue]) -> object:
        """Create a set command for this location.

        Args:
            value: Value to write (literal or RValue)

        Returns:
            SetCmd that writes the value when executed

        Example:
            >>> ref.set(42).execute(ctx)
            >>> ref.set(other_ref.get()).execute(ctx)  # Chain refs
        """
        return result(self.value_type, SetCmd(self, literal(value)))

    def remove(self) -> BoolValue:
        """Create a delete command for this location.

        Returns:
            DeleteCmd that removes the value when executed

        Example:
            >>> ref.remove().execute(ctx)
        """
        return BoolValue(DeleteCmd(self))

    def exists(self) -> BoolValue:
        """Create an existence check operation.

        Returns:
            ExistsOp that returns True if location exists

        Example:
            >>> if ref.exists().execute(ctx):
            ...     print("Value exists")
        """
        return BoolValue(ExistsOp(self))

    def missing(self) -> BoolValue:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if location doesn't exist

        Example:
            >>> if ref.missing().execute(ctx):
            ...     ref.set(default_value).execute(ctx)
        """
        return BoolValue(MissingOp(self))

    def on_change(self) -> OnPrimitiveChangeOp:
        """Create change subscription operation for this value.

        Returns a ChangeOp that subscribes to changes on this primitive value
        via the parent view's ChildObservable protocol.

        Returns:
            OnPrimitiveChangeOp that creates subscription when executed

        Example:
            >>> Once(User.name.on_change(), HandleNameChange())
            >>> OnChange(Config.value.on_change(), SyncConfig())
        """
        return OnPrimitiveChangeOp(self)


class SequenceValueRefBase[T: Value](PrimitiveRefBase[T]):
    """Reference to a primitive value location.

    Points to leaf nodes in the tree: int, str, float, bool, etc.
    Supports read (get) and write (set) operations.

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)

        # Create operations
        User.name.get()         # GetOp[str]
        User.name.set("Alice")  # SetCmd[str]
    """

    pass


class MappingValueRefBase[T: Value](PrimitiveRefBase[T]):
    """Reference to a primitive value location.

    Points to leaf nodes in the tree: int, str, float, bool, etc.
    Supports read (get) and write (set) operations.

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)

        # Create operations
        User.name.get()         # GetOp[str]
        User.name.set("Alice")  # SetCmd[str]
    """

    pass


# =============================================================================
# VIEW REF BASE
# =============================================================================


class ViewRefBase[W, T: Value](ViewRef, ABC):
    """Complete base for container (view) references.

    Provides all standard operations for containers:
    - extract() -> ExtractOp (read entire structure)
    - store(value) -> StoreCmd (write entire structure)
    - clear() -> ClearCmd (remove all items)
    - length() -> LengthOp (query size)
    - exists() -> ExistsOp (check existence)
    - missing() -> MissingOp (check non-existence)

    Type Parameters:
        W: Type of wrapper value (DictValue, ListValue, etc.)
        T: Type of extracted value (dict, list, etc.)
        ContextT: Execution context type
    """

    @abstractmethod
    def result(self, op: RValue) -> W:
        """Convert operations result with corresponding containr."""
        ...

    def extract(self) -> W:
        """Create an extract operation for this container.

        Returns:
            ExtractOp that extracts entire structure when executed

        Example:
            >>> data = dict_ref.extract().execute(ctx)  # Returns dict
        """
        return self.result(ExtractOp(self))

    def store(self, value: T | RValue[T | SpecialValue]) -> W:
        """Create a store command for this container.

        Args:
            value: Value to store (literal or RValue)

        Returns:
            StoreCmd that stores the value when executed

        Example:
            >>> dict_ref.store({"key": "value"}).execute(ctx)
        """
        return self.result(StoreCmd(self, literal(value)))

    def clear(self) -> NoneValue:
        """Create a clear command for this container.

        Returns:
            ClearCmd that clears all items when executed

        Example:
            >>> list_ref.clear().execute(ctx)
        """
        return NoneValue(ClearCmd(self))

    def length(self) -> IntValue:
        """Create a length query operation.

        Returns:
            LengthOp that returns length when executed

        Example:
            >>> count = list_ref.length().execute(ctx)
        """
        return IntValue(LengthOp(self))

    def exists(self) -> BoolValue:
        """Create an existence check operation.

        Returns:
            ExistsOp that returns True if container exists
        """
        return BoolValue(ExistsOp(self))

    def missing(self) -> BoolValue:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if container doesn't exist
        """
        return BoolValue(MissingOp(self))

    def on_change(self) -> OnChangeOp:
        """Subscribe to all changes in this view.

        Returns:
            OnChangeOp that creates subscription when executed

        Example:
            >>> OnChange(User.profile.on_change(), SyncProfile())
        """
        return OnChangeOp(self)

    def on_child_change(self, address: str | RValue[str]) -> OnChildChangeOp:
        """Subscribe to changes on a specific child.

        Args:
            address: Child address to watch

        Returns:
            OnChildChangeOp that creates subscription when executed

        Example:
            >>> OnChange(User.profile.on_child_change("email"), HandleEmailChange())
        """
        return OnChildChangeOp(self, address)

    def on_children_change(self) -> OnChildrenChangeOp:
        """Subscribe to changes on all children.

        Returns:
            OnChildrenChangeOp that creates subscription when executed

        Example:
            >>> OnChange(Users.on_children_change(), SyncUsers())
        """
        return OnChildrenChangeOp(self)

    def on_descendants_change(self, *pattern: key.KeySegment) -> OnDescendantsChangeOp:
        """Subscribe to changes on descendants matching a pattern.

        Args:
            *pattern: Key segments pattern (use "*" for wildcards)

        Returns:
            OnDescendantsChangeOp that creates subscription when executed

        Example:
            >>> OnChange(Users.on_descendants_change("*", "status"), HandleStatusChanges())
        """
        return OnDescendantsChangeOp(self, *pattern)


# =============================================================================
# SEQUENCE REF BASE
# =============================================================================


class SequenceRefBase[W, T: Value, ItemRefT, SliceRefT](ViewRefBase[ListValue, PySequence]):
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

    def _create_item_ref(self, index: int | RValue[int]) -> ItemRefT:
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
    def __getitem__(self, key: RValue[int]) -> ItemRefT: ...

    def __getitem__(self, key: int | slice | RValue[int]) -> ItemRefT | SliceRefT:
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

    def map[R: Value](self, func: Callable[[T], R]) -> ListValue[ItemRefT]:
        """Map a function over sequence elements.

        Args:
            func: Function to apply to each element

        Returns:
            MapOp that applies func at execution time

        Example:
            >>> doubled = list_ref.map(lambda x: x * 2).execute(ctx)
        """
        return ListValue(MapOp(self, func))

    def filter(self, predicate: Callable[[T], bool]) -> ListValue[T]:
        """Filter sequence elements by predicate.

        Args:
            predicate: Function returning True for elements to keep

        Returns:
            ListValue containing filtered elements at execution time

        Example:
            >>> evens = list_ref.filter(lambda x: x % 2 == 0).execute(ctx)
        """
        return ListValue(FilterOp(self, predicate))

    @overload
    def reduce(self, func: Callable[[int, T], int], initial: int) -> IntValue: ...

    @overload
    def reduce(self, func: Callable[[str, T], str], initial: str) -> StrValue: ...

    @overload
    def reduce(self, func: Callable[[float, T], float], initial: float) -> FloatValue: ...

    @overload
    def reduce(self, func: Callable[[bool, T], bool], initial: bool) -> BoolValue: ...

    @overload
    def reduce[V](
        self, func: Callable[[list[V], T], list[V]], initial: list[V]
    ) -> ListValue[V]: ...

    @overload
    def reduce[K, V](
        self, func: Callable[[dict[K, V], T], dict[K, V]], initial: dict[K, V]
    ) -> DictValue[K, V]: ...

    def reduce[R](self, func: Callable[[R, T], R], initial: R) -> object:
        """Reduce sequence to single value.

        Args:
            func: Function (accumulator, element) -> accumulator
            initial: Starting value for accumulator

        Returns:
            Typed value wrapper containing reduced value at execution time

        Example:
            >>> total = list_ref.reduce(lambda acc, x: acc + x, 0).execute(ctx)
        """
        return result(type(initial), ReduceOp(self, func, initial))

    @overload
    def find(
        self: SequenceRefBase[W, int, ItemRefT, SliceRefT], predicate: Callable[[int], bool]
    ) -> IntValue: ...

    @overload
    def find(
        self: SequenceRefBase[W, str, ItemRefT, SliceRefT], predicate: Callable[[str], bool]
    ) -> StrValue: ...

    @overload
    def find(
        self: SequenceRefBase[W, float, ItemRefT, SliceRefT], predicate: Callable[[float], bool]
    ) -> FloatValue: ...

    @overload
    def find(
        self: SequenceRefBase[W, bool, ItemRefT, SliceRefT], predicate: Callable[[bool], bool]
    ) -> BoolValue: ...

    @overload
    def find[V](
        self: SequenceRefBase[W, list[V], ItemRefT, SliceRefT], predicate: Callable[[list[V]], bool]
    ) -> ListValue[V]: ...

    @overload
    def find[K, V](
        self: SequenceRefBase[W, dict[K, V], ItemRefT, SliceRefT],
        predicate: Callable[[dict[K, V]], bool],
    ) -> DictValue[K, V]: ...

    def find(self, predicate: Callable[[T], bool]) -> object:
        """Find first element matching predicate.

        Args:
            predicate: Function returning True for element to find

        Returns:
            Typed value wrapper containing element at execution time

        Example:
            >>> first_even = list_ref.find(lambda x: x % 2 == 0).execute(ctx)
        """
        return result(self.item_type, FindOp(self, predicate))

    def find_index(self, predicate: Callable[[T], bool]) -> IntValue:
        """Find index of first element matching predicate.

        Args:
            predicate: Function returning True for element to find

        Returns:
            IntValue containing index at execution time

        Example:
            >>> idx = list_ref.find_index(lambda x: x > 10).execute(ctx)
        """
        return IntValue(FindIndexOp(self, predicate))

    def index(self, value: T) -> IntValue:
        """Find index of value in sequence.

        Args:
            value: Value to search for

        Returns:
            IntValue containing index at execution time

        Example:
            >>> idx = list_ref.index("apple").execute(ctx)
        """
        return IntValue(IndexOp(self, value))

    def count(self, value: T) -> IntValue:
        """Count occurrences of value in sequence.

        Args:
            value: Value to count

        Returns:
            IntValue containing count at execution time

        Example:
            >>> n = list_ref.count("apple").execute(ctx)
        """
        return IntValue(CountOp(self, value))


class MutableSequenceRefBase[W, T: Value, ItemRefT, SliceRefT](
    SequenceRefBase[W, T, ItemRefT, SliceRefT]
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

    def append(self, value: T | RValue[T | SpecialValue]) -> NoneValue:
        """Create an append command.

        Args:
            value: Item to append (literal or RValue)

        Returns:
            NoneValue (append returns None after execution)

        Example:
            >>> list_ref.append(42).execute(ctx)
        """
        return NoneValue(AppendCmd(self, literal(value)))

    def insert(
        self,
        index: int | RValue[int | SpecialValue],
        value: T | RValue[T | SpecialValue],
    ) -> NoneValue:
        """Create an insert command.

        Args:
            index: Position to insert at
            value: Item to insert (literal or RValue)

        Returns:
            NoneValue (insert returns None after execution)

        Example:
            >>> list_ref.insert(0, "first").execute(ctx)
        """
        return NoneValue(InsertCmd(self, literal(index), literal(value)))

    @overload
    def pop(
        self: MutableSequenceRefBase[W, int, ItemRefT, SliceRefT],
        index: int | RValue[int | SpecialValue] | None = None,
    ) -> IntValue: ...

    @overload
    def pop(
        self: MutableSequenceRefBase[W, str, ItemRefT, SliceRefT],
        index: int | RValue[int | SpecialValue] | None = None,
    ) -> StrValue: ...

    @overload
    def pop(
        self: MutableSequenceRefBase[W, float, ItemRefT, SliceRefT],
        index: int | RValue[int | SpecialValue] | None = None,
    ) -> FloatValue: ...

    @overload
    def pop(
        self: MutableSequenceRefBase[W, bool, ItemRefT, SliceRefT],
        index: int | RValue[int | SpecialValue] | None = None,
    ) -> BoolValue: ...

    @overload
    def pop[V](
        self: MutableSequenceRefBase[W, list[V], ItemRefT, SliceRefT],
        index: int | RValue[int | SpecialValue] | None = None,
    ) -> ListValue[V]: ...

    @overload
    def pop[K, V](
        self: MutableSequenceRefBase[W, dict[K, V], ItemRefT, SliceRefT],
        index: int | RValue[int | SpecialValue] | None = None,
    ) -> DictValue[K, V]: ...

    def pop(self, index: int | RValue[int | SpecialValue] | None = None) -> object:
        """Create a pop command.

        Args:
            index: Position to pop from (default: last)

        Returns:
            Typed value wrapper containing removed item at execution time

        Example:
            >>> last = list_ref.pop().execute(ctx)
            >>> first = list_ref.pop(0).execute(ctx)
        """
        wrapped_index = literal(index) if index is not None else None
        return result(self.item_type, PopCmd(self, wrapped_index))


# =============================================================================
# MAPPING REF BASE
# =============================================================================


class MappingRefBase[W, K, V: Value, ChildRefT](ViewRefBase[W, PyMapping[K, V]]):
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

    def _create_child_ref(self, key: K | RValue[K]) -> ChildRefT:
        """Create a reference to a child. Override in subclass.

        Args:
            key: Child key

        Returns:
            Reference to child at key
        """
        raise NotImplementedError("Subclass must implement _create_child_ref")

    def __getitem__(self, key: K | RValue[K]) -> ChildRefT:
        """Get child reference by key.

        Args:
            key: Key value

        Returns:
            Reference to item at key

        Example:
            >>> user_ref = users_ref["alice"]
        """
        return self._create_child_ref(key)

    def keys(self) -> ListValue[K]:
        """Create a keys query operation.

        Returns:
            ListValue containing all keys when executed

        Example:
            >>> all_keys = dict_ref.keys().execute(ctx)
        """
        return ListValue(KeysOp(self))

    def values(self) -> ListValue[V]:
        """Create a values query operation.

        Returns:
            ListValue containing all values when executed

        Example:
            >>> all_values = dict_ref.values().execute(ctx)
        """
        return ListValue(ValuesOp(self))

    def items(self) -> ListValue[tuple[K, V]]:
        """Create an items query operation.

        Returns:
            ListValue containing all (key, value) pairs when executed

        Example:
            >>> all_items = dict_ref.items().execute(ctx)
        """
        return ListValue(ItemsOp(self))

    def map_values[R: Value](self, func: Callable[[V], R]) -> DictValue[K, R]:
        """Map function over mapping values.

        Args:
            func: Function to apply to each value

        Returns:
            DictValue containing transformed dict at execution time

        Example:
            >>> doubled = scores_ref.map_values(lambda x: x * 2).execute(ctx)
        """
        return DictValue(MapValuesOp(self, func))

    def map_items[K2, V2: Value](self, func: Callable[[K, V], tuple[K2, V2]]) -> DictValue[K2, V2]:
        """Map function over mapping items.

        Args:
            func: Function (key, value) -> (new_key, new_value)

        Returns:
            DictValue containing transformed dict at execution time

        Example:
            >>> upper_keys = dict_ref.map_items(lambda k, v: (k.upper(), v)).execute(ctx)
        """
        return DictValue(MapItemsOp(self, func))

    def filter(self, predicate: Callable[[K, V], bool]) -> DictValue[K, V]:
        """Filter mapping items by predicate.

        Args:
            predicate: Function (key, value) -> bool, keep if True

        Returns:
            DictValue containing filtered dict at execution time

        Example:
            >>> high_scores = scores_ref.filter(lambda k, v: v > 100).execute(ctx)
        """
        return DictValue(FilterItemsOp(self, predicate))

    @overload
    def reduce(self, func: Callable[[int, K, V], int], initial: int) -> IntValue: ...

    @overload
    def reduce(self, func: Callable[[str, K, V], str], initial: str) -> StrValue: ...

    @overload
    def reduce(self, func: Callable[[float, K, V], float], initial: float) -> FloatValue: ...

    @overload
    def reduce(self, func: Callable[[bool, K, V], bool], initial: bool) -> BoolValue: ...

    @overload
    def reduce[V2](
        self, func: Callable[[list[V2], K, V], list[V2]], initial: list[V2]
    ) -> ListValue[V2]: ...

    @overload
    def reduce[K2, V2](
        self, func: Callable[[dict[K2, V2], K, V], dict[K2, V2]], initial: dict[K2, V2]
    ) -> DictValue[K2, V2]: ...

    def reduce[R](self, func: Callable[[R, K, V], R], initial: R) -> object:
        """Reduce mapping to single value.

        Args:
            func: Function (accumulator, key, value) -> new_accumulator
            initial: Starting value for accumulator

        Returns:
            Typed value wrapper containing reduced value at execution time

        Example:
            >>> total = scores_ref.reduce(lambda acc, k, v: acc + v, 0).execute(ctx)
        """
        return result(type(initial), ReduceItemsOp(self, func, initial))

    @overload
    def find_key(
        self: MappingRefBase[W, int, V, ChildRefT], predicate: Callable[[V], bool]
    ) -> IntValue: ...

    @overload
    def find_key(
        self: MappingRefBase[W, str, V, ChildRefT], predicate: Callable[[V], bool]
    ) -> StrValue: ...

    @overload
    def find_key(
        self: MappingRefBase[W, float, V, ChildRefT], predicate: Callable[[V], bool]
    ) -> FloatValue: ...

    @overload
    def find_key(
        self: MappingRefBase[W, bool, V, ChildRefT], predicate: Callable[[V], bool]
    ) -> BoolValue: ...

    def find_key(self, predicate: Callable[[V], bool]) -> object:
        """Find first key whose value matches predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            Typed value wrapper containing matching key at execution time

        Example:
            >>> winner = scores_ref.find_key(lambda v: v >= 100).execute(ctx)
        """
        return result(self.key_type, FindKeyOp(self, predicate))

    @overload
    def find_value(
        self: MappingRefBase[W, K, int, ChildRefT], predicate: Callable[[int], bool]
    ) -> IntValue: ...

    @overload
    def find_value(
        self: MappingRefBase[W, K, str, ChildRefT], predicate: Callable[[str], bool]
    ) -> StrValue: ...

    @overload
    def find_value(
        self: MappingRefBase[W, K, float, ChildRefT], predicate: Callable[[float], bool]
    ) -> FloatValue: ...

    @overload
    def find_value(
        self: MappingRefBase[W, K, bool, ChildRefT], predicate: Callable[[bool], bool]
    ) -> BoolValue: ...

    @overload
    def find_value[V2](
        self: MappingRefBase[W, K, list[V2], ChildRefT], predicate: Callable[[list[V2]], bool]
    ) -> ListValue[V2]: ...

    @overload
    def find_value[K2, V2](
        self: MappingRefBase[W, K, dict[K2, V2], ChildRefT],
        predicate: Callable[[dict[K2, V2]], bool],
    ) -> DictValue[K2, V2]: ...

    def find_value(self, predicate: Callable[[V], bool]) -> object:
        """Find first value matching predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            Typed value wrapper containing matching value at execution time

        Example:
            >>> high_score = scores_ref.find_value(lambda v: v >= 100).execute(ctx)
        """
        return result(self.value_type, FindValueOp(self, predicate))

    def find_item(self, predicate: Callable[[K, V], bool]) -> TupleValue[K, V]:
        """Find first item (key, value) matching predicate.

        Args:
            predicate: Function (key, value) -> bool

        Returns:
            TupleValue containing matching (key, value) tuple at execution time

        Example:
            >>> item = dict_ref.find_item(lambda k, v: k.startswith("admin")).execute(ctx)
        """
        return TupleValue(FindItemOp(self, predicate))


class MutableMappingRefBase[W, K, V: Value, ChildRefT](MappingRefBase[W, K, V, ChildRefT]):
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


class SetRefBase[T: Value](ViewRefBase[SetValue, PySet[T]]):
    """Complete base for read-only set references.

    Extends ViewRefBase for set semantics.

    Type Parameters:
        T: Type of items in the set
        ContextT: Execution context type
    """

    pass


class MutableSetRefBase[T: Value](SetRefBase[T]):
    """Complete base for mutable set references.

    Extends SetRefBase with mutation capabilities:
    - add(value) -> AddCmd
    - remove(value) -> RemoveCmd (raises error if missing)
    - discard(value) -> DiscardCmd (no error if missing)

    Type Parameters:
        T: Type of items in the set
        ContextT: Execution context type
    """

    def add(self, value: T | RValue[T | SpecialValue]) -> NoneValue:
        """Create an add command.

        Args:
            value: Item to add (literal or RValue)

        Returns:
            NoneValue (add returns None after execution)

        Example:
            >>> set_ref.add("item").execute(ctx)
        """
        return NoneValue(AddCmd(self, literal(value)))

    def remove(self, value: T | RValue[T | SpecialValue]) -> NoneValue:
        """Create a remove command.

        Args:
            value: Item to remove (literal or RValue)

        Returns:
            NoneValue (remove returns None after execution)

        Note:
            Raises KeyError at execution if item not found.

        Example:
            >>> set_ref.remove("item").execute(ctx)
        """
        return NoneValue(RemoveCmd(self, literal(value)))

    def discard(self, value: T | RValue[T | SpecialValue]) -> NoneValue:
        """Create a discard command.

        Args:
            value: Item to discard (literal or RValue)

        Returns:
            NoneValue (discard returns None after execution, no error if missing)

        Example:
            >>> set_ref.discard("item").execute(ctx)  # No error if missing
        """
        return NoneValue(DiscardCmd(self, literal(value)))
