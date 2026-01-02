"""Capability implementation bases for LValue references.

This module provides mixin classes that IMPLEMENT capability protocols.
These are the building blocks that get combined to create
complete ref implementations.

Each base implements methods from the corresponding capability protocol:
- ExistableBase implements Existable (exists(), missing())
- GettableBase implements Gettable (get())
- SettableBase implements Settable (set())
- etc.

These are NOT protocols - they are concrete implementations that can be
mixed into ref classes.

Usage:
    class MyRef(ExistableBase, GettableBase, SettableBase, PrimitiveRef):
        # Gets exists(), missing(), get(), set() implementations
        pass
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

from ..computations.commands import (
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
from ..computations.reactive_ops import (
    OnChangeOp,
    OnChildChangeOp,
    OnChildrenChangeOp,
    OnDescendantsChangeOp,
    OnPrimitiveChangeOp,
)
from ..computations.ref_ops import (
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
from ..values.conversion import computed, literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.loc import key
    from everyshape.types import SpecialValue

    from ..term import RValue


__all__ = [  # noqa: RUF022
    "UnionRefBases",
    # Core capability bases
    "ExistableBase",
    "GettableBase",
    "SettableBase",
    "DeletableBase",
    "ExtractableBase",
    "StorableBase",
    "ClearableBase",
    "LengthableBase",
    # Observable bases
    "PrimitiveObservableBase",
    "ViewObservableBase",
    # Query bases
    "KeysQueryableBase",
    "ValuesQueryableBase",
    "ItemsQueryableBase",
    # Sequence capability bases
    "SequenceIndexableBase",
    "SequenceIterableBase",
    "AppendableBase",
    "InsertableBase",
    "PoppableBase",
    # Mapping capability bases
    "MappingNestableBase",
    "MappingIterableBase",
    # Set capability bases
    "SetAddableBase",
    "SetRemovableBase",
]

type UnionRefBases = (
    ExistableBase
    | GettableBase
    | SettableBase
    | DeletableBase
    | ExtractableBase
    | StorableBase
    | ClearableBase
    | LengthableBase
    | PrimitiveObservableBase
    | ViewObservableBase
    | KeysQueryableBase
    | ValuesQueryableBase
    | ItemsQueryableBase
    | SequenceIndexableBase
    | SequenceIterableBase
    | AppendableBase
    | InsertableBase
    | PoppableBase
    | MappingNestableBase
    | MappingIterableBase
    | SetAddableBase
    | SetRemovableBase
)


# =============================================================================
# EXISTENCE CAPABILITY BASE
# =============================================================================


class ExistableBase:
    """Implementation base for existence checking.

    Implements the Existable protocol with exists() and missing() methods.
    Requires self to have resolve() method.
    """

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


# =============================================================================
# READ CAPABILITY BASES
# =============================================================================


class GettableBase[T]:
    """Implementation base for getting primitive values.

    Implements the Gettable protocol with get() method.
    Requires self to have value_type attribute.
    """

    value_type: type[T]

    # Primitives
    @overload
    def get(self: GettableBase[int]) -> IntValue: ...

    @overload
    def get(self: GettableBase[str]) -> StrValue: ...

    @overload
    def get(self: GettableBase[bool]) -> BoolValue: ...

    @overload
    def get(self: GettableBase[float]) -> FloatValue: ...

    @overload
    def get(self: GettableBase[bytes]) -> BytesValue: ...

    @overload
    def get(self: GettableBase[None]) -> NoneValue: ...

    # Collections
    @overload
    def get[V](self: GettableBase[list[V]]) -> ListValue[V]: ...

    @overload
    def get[K, V](self: GettableBase[dict[K, V]]) -> DictValue[K, V]: ...

    @overload
    def get[V](self: GettableBase[set[V]]) -> SetValue[V]: ...

    def get(self) -> object:
        """Create a get operation for this location.

        Returns:
            GetOp that reads the value when executed

        Example:
            >>> value = ref.get().execute(ctx)
        """
        return computed(self.value_type, GetOp(self))


class ExtractableBase[W](ABC):
    """Implementation base for extracting container contents.

    Implements the Extractable protocol with extract() method.
    """

    @abstractmethod
    def result(self, op: RValue) -> W:
        """Wrap an operation result in the appropriate typed value container.

        Args:
            op: The operation to wrap

        Returns:
            Typed value wrapper (e.g., ListValue, DictValue, SetValue)

        Note:
            Subclasses must implement this to return the correct wrapper type.

        Example:
            def result(self, op: RValue) -> ListValue[T]:
                return ListValue(op)
        """
        ...

    def extract(self) -> W:
        """Create an extract operation for this container.

        Returns:
            ExtractOp that extracts entire structure when executed

        Example:
            >>> data = dict_ref.extract().execute(ctx)  # Returns dict
        """
        return self.result(ExtractOp(self))


# =============================================================================
# WRITE CAPABILITY BASES
# =============================================================================


class SettableBase[T]:
    """Implementation base for setting primitive values.

    Implements the Settable protocol with set() method.
    Requires self to have value_type attribute.
    """

    value_type: type[T]

    @overload
    def set(
        self: SettableBase[int], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> IntValue: ...

    @overload
    def set(
        self: SettableBase[str], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> StrValue: ...

    @overload
    def set(
        self: SettableBase[bool], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> BoolValue: ...

    @overload
    def set(
        self: SettableBase[float], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> FloatValue: ...

    @overload
    def set(
        self: SettableBase[bytes], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> BytesValue: ...

    @overload
    def set(
        self: SettableBase[None], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> NoneValue: ...

    # Collections
    @overload
    def set[V](
        self: SettableBase[list[V]], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> ListValue[V]: ...

    @overload
    def set[K, V](
        self: SettableBase[dict[K, V]], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> DictValue[K, V]: ...

    @overload
    def set[V](
        self: SettableBase[set[V]], value: T | SpecialValue | RValue[T | SpecialValue]
    ) -> SetValue[V]: ...

    def set(self, value: T | SpecialValue | RValue[T | SpecialValue]) -> object:
        """Create a set command for this location.

        Args:
            value: Value to write (literal or RValue)

        Returns:
            SetCmd that writes the value when executed

        Example:
            >>> ref.set(42).execute(ctx)
            >>> ref.set(other_ref.get()).execute(ctx)  # Chain refs
        """
        return computed(self.value_type, SetCmd(self, literal(value)))


class StorableBase[W, T](ABC):
    """Implementation base for storing container contents.

    Implements the Storable protocol with store() method.
    """

    @abstractmethod
    def result(self, op: RValue) -> W:
        """Wrap an operation result in the appropriate typed value container.

        Args:
            op: The operation to wrap

        Returns:
            Typed value wrapper (e.g., ListValue, DictValue, SetValue)

        Note:
            Subclasses must implement this to return the correct wrapper type.

        Example:
            def result(self, op: RValue) -> DictValue[K, V]:
                return DictValue(op)
        """
        ...

    def store(self, value: T | SpecialValue | RValue[T | SpecialValue]) -> W:
        """Create a store command for this container.

        Args:
            value: Value to store (literal or RValue)

        Returns:
            StoreCmd that stores the value when executed

        Example:
            >>> dict_ref.store({"key": "value"}).execute(ctx)
        """
        return self.result(StoreCmd(self, literal(value)))


# =============================================================================
# DELETE CAPABILITY BASES
# =============================================================================


class DeletableBase:
    """Implementation base for deleting values.

    Implements the Deletable protocol with remove() method.
    """

    def remove(self) -> NoneValue:
        """Create a delete command for this location.

        Returns:
            DeleteCmd that removes the value when executed

        Example:
            >>> ref.remove().execute(ctx)
        """
        return NoneValue(DeleteCmd(self))


class ClearableBase:
    """Implementation base for clearing containers.

    Implements the Clearable protocol with clear() method.
    """

    def clear(self) -> NoneValue:
        """Create a clear command for this container.

        Returns:
            ClearCmd that clears all items when executed

        Example:
            >>> list_ref.clear().execute(ctx)
        """
        return NoneValue(ClearCmd(self))


# =============================================================================
# LENGTH CAPABILITY BASE
# =============================================================================


class LengthableBase:
    """Implementation base for length queries.

    Implements the Lengthable protocol with length() method.
    """

    def length(self) -> IntValue:
        """Create a length query operation.

        Returns:
            LengthOp that returns length when executed

        Example:
            >>> count = list_ref.length().execute(ctx)
        """
        return IntValue(LengthOp(self))


# =============================================================================
# OBSERVABLE CAPABILITY BASES
# =============================================================================


class PrimitiveObservableBase:
    """Implementation base for primitive value observation.

    Implements observation for leaf values via parent view's ChildObservable.
    """

    def on_change(self) -> OnPrimitiveChangeOp:
        """Create change subscription operation for this value.

        Returns:
            OnPrimitiveChangeOp that creates subscription when executed

        Example:
            >>> Once(User.name.on_change(), HandleNameChange())
        """
        return OnPrimitiveChangeOp(self)


class ViewObservableBase:
    """Implementation base for container observation.

    Implements observation for containers via Observable and ChildObservable protocols.
    """

    def on_change(self) -> OnChangeOp:
        """Subscribe to all changes in this view.

        Returns:
            OnChangeOp that creates subscription when executed

        Example:
            >>> OnChange(User.profile.on_change(), SyncProfile())
        """
        return OnChangeOp(self)

    def on_child_change(
        self, address: str | SpecialValue | RValue[str | SpecialValue]
    ) -> OnChildChangeOp:
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
# QUERY CAPABILITY BASES
# =============================================================================


class KeysQueryableBase[K]:
    """Implementation base for keys queries.

    Implements the KeysQueryable protocol with keys() method.
    """

    def keys(self) -> ListValue[K]:
        """Create a keys query operation.

        Returns:
            ListValue containing all keys when executed

        Example:
            >>> all_keys = dict_ref.keys().execute(ctx)
        """
        return ListValue(KeysOp(self))


class ValuesQueryableBase[V]:
    """Implementation base for values queries.

    Implements the ValuesQueryable protocol with values() method.
    """

    def values(self) -> ListValue[V]:
        """Create a values query operation.

        Returns:
            ListValue containing all values when executed

        Example:
            >>> all_values = dict_ref.values().execute(ctx)
        """
        return ListValue(ValuesOp(self))


class ItemsQueryableBase[K, V]:
    """Implementation base for items queries.

    Implements the ItemsQueryable protocol with items() method.
    """

    def items(self) -> ListValue[tuple[K, V]]:
        """Create an items query operation.

        Returns:
            ListValue containing all (key, value) pairs when executed

        Example:
            >>> all_items = dict_ref.items().execute(ctx)
        """
        return ListValue(ItemsOp(self))


# =============================================================================
# SEQUENCE CAPABILITY BASES
# =============================================================================


class SequenceIndexableBase[T, ItemRefT, SliceRefT](ABC):
    """Implementation base for sequence indexing.

    Provides __getitem__ for integer and slice access.
    Subclasses must implement _create_item_ref and _create_slice_ref.
    """

    @abstractmethod
    def _create_item_ref(self, index: int | SpecialValue | RValue[int | SpecialValue]) -> ItemRefT:
        """Create a reference to an item at the given index.

        Args:
            index: Item index (int or RValue[int] for computed index)

        Returns:
            Reference to item at the specified index

        Note:
            Subclasses must implement this to return the appropriate ref type.

        Example:
            def _create_item_ref(self, index: int | RValue[int]) -> ItemRef:
                return ItemRef(self, index)
        """
        ...

    @abstractmethod
    def _create_slice_ref(self, key: slice) -> SliceRefT:
        """Create a reference to a slice of the sequence.

        Args:
            key: Slice specification (start:stop:step)

        Returns:
            Reference to the specified slice

        Note:
            Subclasses must implement this to return the appropriate ref type.

        Example:
            def _create_slice_ref(self, key: slice) -> SliceRef:
                return SliceRef(self, key)
        """
        ...

    @overload
    def __getitem__(self, key: int) -> ItemRefT: ...

    @overload
    def __getitem__(self, key: slice) -> SliceRefT: ...

    @overload
    def __getitem__(self, key: RValue[int | SpecialValue]) -> ItemRefT: ...

    def __getitem__(
        self, key: int | slice | SpecialValue | RValue[int | SpecialValue]
    ) -> ItemRefT | SliceRefT:
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


class SequenceIterableBase[T]:
    """Implementation base for sequence iteration operations.

    Provides map(), filter(), reduce(), find(), find_index(), index(), count().
    Requires self to have item_type attribute.
    """

    item_type: type[T]

    def map[R](self, func: Callable[[T], R]) -> ListValue[R]:
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
        return computed(type(initial), ReduceOp(self, func, initial))

    @overload
    def find(self: SequenceIterableBase[int], predicate: Callable[[int], bool]) -> IntValue: ...

    @overload
    def find(self: SequenceIterableBase[str], predicate: Callable[[str], bool]) -> StrValue: ...

    @overload
    def find(
        self: SequenceIterableBase[float], predicate: Callable[[float], bool]
    ) -> FloatValue: ...

    @overload
    def find(self: SequenceIterableBase[bool], predicate: Callable[[bool], bool]) -> BoolValue: ...

    @overload
    def find[V](
        self: SequenceIterableBase[list[V]], predicate: Callable[[list[V]], bool]
    ) -> ListValue[V]: ...

    @overload
    def find[K, V](
        self: SequenceIterableBase[dict[K, V]],
        predicate: Callable[[dict[K, V]], bool],
    ) -> DictValue[K, V]: ...

    def find(self, predicate: Callable) -> object:
        """Find first element matching predicate.

        Args:
            predicate: Function returning True for element to find

        Returns:
            Typed value wrapper containing element at execution time

        Example:
            >>> first_even = list_ref.find(lambda x: x % 2 == 0).execute(ctx)
        """
        return computed(self.item_type, FindOp(self, predicate))

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

    def index(self, value: T | SpecialValue) -> IntValue:
        """Find index of value in sequence.

        Args:
            value: Value to search for

        Returns:
            IntValue containing index at execution time

        Example:
            >>> idx = list_ref.index("apple").execute(ctx)
        """
        return IntValue(IndexOp(self, value))

    def count(self, value: T | SpecialValue) -> IntValue:
        """Count occurrences of value in sequence.

        Args:
            value: Value to count

        Returns:
            IntValue containing count at execution time

        Example:
            >>> n = list_ref.count("apple").execute(ctx)
        """
        return IntValue(CountOp(self, value))


class AppendableBase[T]:
    """Implementation base for appending to sequences.

    Implements the Appendable protocol with append() method.
    """

    def append(self, value: T | SpecialValue | RValue[T | SpecialValue]) -> NoneValue:
        """Create an append command.

        Args:
            value: Item to append (literal or RValue)

        Returns:
            NoneValue (append returns None after execution)

        Example:
            >>> list_ref.append(42).execute(ctx)
        """
        return NoneValue(AppendCmd(self, literal(value)))


class InsertableBase[T]:
    """Implementation base for inserting into sequences.

    Implements the Insertable protocol with insert() method.
    """

    def insert(
        self,
        index: int | SpecialValue | RValue[int | SpecialValue],
        value: T | SpecialValue | RValue[T | SpecialValue],
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


class PoppableBase[T]:
    """Implementation base for popping from sequences.

    Implements the Poppable protocol with pop() method.
    Requires self to have item_type attribute.
    """

    item_type: type[T]

    @overload
    def pop(
        self: PoppableBase[int],
        index: int | SpecialValue | RValue[int | SpecialValue] | None = None,
    ) -> IntValue: ...

    @overload
    def pop(
        self: PoppableBase[str],
        index: int | SpecialValue | RValue[int | SpecialValue] | None = None,
    ) -> StrValue: ...

    @overload
    def pop(
        self: PoppableBase[float],
        index: int | SpecialValue | RValue[int | SpecialValue] | None = None,
    ) -> FloatValue: ...

    @overload
    def pop(
        self: PoppableBase[bool],
        index: int | SpecialValue | RValue[int | SpecialValue] | None = None,
    ) -> BoolValue: ...

    @overload
    def pop[V](
        self: PoppableBase[list[V]],
        index: int | SpecialValue | RValue[int | SpecialValue] | None = None,
    ) -> ListValue[V]: ...

    @overload
    def pop[K, V](
        self: PoppableBase[dict[K, V]],
        index: int | SpecialValue | RValue[int | SpecialValue] | None = None,
    ) -> DictValue[K, V]: ...

    def pop(self, index: int | SpecialValue | RValue[int | SpecialValue] | None = None) -> object:
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
        return computed(self.item_type, PopCmd(self, wrapped_index))


# =============================================================================
# MAPPING CAPABILITY BASES
# =============================================================================


class MappingNestableBase[K, ChildRefT]:
    """Implementation base for mapping navigation.

    Provides __getitem__ for key-based child access.
    Subclasses must implement _create_child_ref.
    """

    @abstractmethod
    def _create_child_ref(self, key: K | SpecialValue | RValue[K | SpecialValue]) -> ChildRefT:
        """Create a reference to a child at the given key.

        Args:
            key: Child key (literal or RValue[K] for computed key)

        Returns:
            Reference to child at the specified key

        Note:
            Subclasses must implement this to return the appropriate ref type.

        Example:
            def _create_child_ref(self, key: K | RValue[K]) -> ChildRef:
                return ChildRef(self, key)
        """
        ...

    def __getitem__(self, key: K | SpecialValue | RValue[K | SpecialValue]) -> ChildRefT:
        """Get child reference by key.

        Args:
            key: Key value

        Returns:
            Reference to item at key

        Example:
            >>> user_ref = users_ref["alice"]
        """
        return self._create_child_ref(key)


class MappingIterableBase[K, V]:
    """Implementation base for mapping iteration operations.

    Provides map_values(), map_items(), filter(), reduce(),
    find_key(), find_value(), find_item().
    Requires self to have key_type and value_type attributes.
    """

    key_type: type[K]
    value_type: type[V]

    def map_values[R](self, func: Callable[[V], R]) -> DictValue[K, R]:
        """Map function over mapping values.

        Args:
            func: Function to apply to each value

        Returns:
            DictValue containing transformed dict at execution time

        Example:
            >>> doubled = scores_ref.map_values(lambda x: x * 2).execute(ctx)
        """
        return DictValue(MapValuesOp(self, func))

    def map_items[K2, V2](self, func: Callable[[K, V], tuple[K2, V2]]) -> DictValue[K2, V2]:
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
        return computed(type(initial), ReduceItemsOp(self, func, initial))

    @overload
    def find_key(self: MappingIterableBase[int, V], predicate: Callable[[V], bool]) -> IntValue: ...

    @overload
    def find_key(self: MappingIterableBase[str, V], predicate: Callable[[V], bool]) -> StrValue: ...

    @overload
    def find_key(
        self: MappingIterableBase[float, V], predicate: Callable[[V], bool]
    ) -> FloatValue: ...

    @overload
    def find_key(
        self: MappingIterableBase[bool, V], predicate: Callable[[V], bool]
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
        return computed(self.key_type, FindKeyOp(self, predicate))

    @overload
    def find_value(
        self: MappingIterableBase[K, int], predicate: Callable[[int], bool]
    ) -> IntValue: ...

    @overload
    def find_value(
        self: MappingIterableBase[K, str], predicate: Callable[[str], bool]
    ) -> StrValue: ...

    @overload
    def find_value(
        self: MappingIterableBase[K, float], predicate: Callable[[float], bool]
    ) -> FloatValue: ...

    @overload
    def find_value(
        self: MappingIterableBase[K, bool], predicate: Callable[[bool], bool]
    ) -> BoolValue: ...

    @overload
    def find_value[V2](
        self: MappingIterableBase[K, list[V2]], predicate: Callable[[list[V2]], bool]
    ) -> ListValue[V2]: ...

    @overload
    def find_value[K2, V2](
        self: MappingIterableBase[K, dict[K2, V2]],
        predicate: Callable[[dict[K2, V2]], bool],
    ) -> DictValue[K2, V2]: ...

    def find_value(self, predicate: Callable) -> object:
        """Find first value matching predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            Typed value wrapper containing matching value at execution time

        Example:
            >>> high_score = scores_ref.find_value(lambda v: v >= 100).execute(ctx)
        """
        return computed(self.value_type, FindValueOp(self, predicate))

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


# =============================================================================
# SET CAPABILITY BASES
# =============================================================================


class SetAddableBase[T]:
    """Implementation base for adding to sets.

    Implements add() method for sets.
    """

    def add(self, value: T | SpecialValue | RValue[T | SpecialValue]) -> NoneValue:
        """Create an add command.

        Args:
            value: Item to add (literal or RValue)

        Returns:
            NoneValue (add returns None after execution)

        Example:
            >>> set_ref.add("item").execute(ctx)
        """
        return NoneValue(AddCmd(self, literal(value)))


class SetRemovableBase[T]:
    """Implementation base for removing from sets.

    Implements remove() and discard() methods for sets.
    """

    def remove(self, value: T | SpecialValue | RValue[T | SpecialValue]) -> NoneValue:
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

    def discard(self, value: T | SpecialValue | RValue[T | SpecialValue]) -> NoneValue:
        """Create a discard command.

        Args:
            value: Item to discard (literal or RValue)

        Returns:
            NoneValue (discard returns None after execution, no error if missing)

        Example:
            >>> set_ref.discard("item").execute(ctx)  # No error if missing
        """
        return NoneValue(DiscardCmd(self, literal(value)))
