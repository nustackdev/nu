"""Sequence capability bases for LValue references.

This module provides sequence-related capability bases:
- SequenceIndexableBase - for index/slice access
- SequenceIterableBase - for functional iteration (map, filter, reduce, etc.)
- AppendableBase - for appending items
- InsertableBase - for inserting items
- PoppableBase - for popping items
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

from everybase import IntValue, ListValue, NoneValue, ensure_term, typed_value


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyabc import Sentinel, Term
    from everybase import BoolValue, DictValue, FloatValue, StrValue


__all__ = [
    "AppendableBase",
    "InsertableBase",
    "PoppableBase",
    "SequenceIndexableBase",
    "SequenceIterableBase",
]


# =============================================================================
# SEQUENCE CAPABILITY BASES
# =============================================================================


class SequenceIndexableBase[ItemT, ItemRefT, SliceRefT](ABC):
    """Implementation base for sequence indexing.

    Provides __getitem__ for integer and slice access.
    Subclasses must implement _create_item_ref and _create_slice_ref.
    """

    @abstractmethod
    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ItemRefT:
        """Create a reference to an item at the given index.

        Args:
            index: Item index (int or Term[int] for computed index)

        Returns:
            Reference to item at the specified index

        Note:
            Subclasses must implement this to return the appropriate ref type.

        Example:
            def _create_item_ref(self, index: int | Term[int]) -> ItemRef:
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
    def __getitem__(self, key: Term[int | Sentinel]) -> ItemRefT: ...

    def __getitem__(
        self, key: int | slice | Sentinel | Term[int | Sentinel]
    ) -> ItemRefT | SliceRefT:
        """Get item or slice reference.

        Args:
            key: Index (int/Term) or slice

        Returns:
            Reference to item or slice

        Example:
            >>> item_ref = list_ref[0]
            >>> slice_ref = list_ref[1:3]
        """
        if isinstance(key, slice):
            return self._create_slice_ref(key)
        return self._create_item_ref(key)


class SequenceIterableBase[ItemT]:
    """Implementation base for sequence iteration operations.

    Provides map(), filter(), reduce(), find(), find_index(), index(), count().
    Requires self to have item_type attribute.
    """

    item_type: type[ItemT]

    def map[R](self, func: Callable[[ItemT], R]) -> ListValue[R]:
        """Map a function over sequence elements.

        Args:
            func: Function to apply to each element

        Returns:
            MapOp that applies func at execution time

        Example:
            >>> doubled = list_ref.map(lambda x: x * 2).execute(ctx)
        """
        from every_pv.morphisms import MapOp

        return ListValue(MapOp(self, func))

    def filter(self, predicate: Callable[[ItemT], bool]) -> ListValue[ItemT]:
        """Filter sequence elements by predicate.

        Args:
            predicate: Function returning True for elements to keep

        Returns:
            ListValue containing filtered elements at execution time

        Example:
            >>> evens = list_ref.filter(lambda x: x % 2 == 0).execute(ctx)
        """
        from every_pv.morphisms import FilterOp

        return ListValue(FilterOp(self, predicate))

    @overload
    def reduce(self, func: Callable[[int, ItemT], int], initial: int) -> IntValue: ...

    @overload
    def reduce(self, func: Callable[[str, ItemT], str], initial: str) -> StrValue: ...

    @overload
    def reduce(self, func: Callable[[float, ItemT], float], initial: float) -> FloatValue: ...

    @overload
    def reduce(self, func: Callable[[bool, ItemT], bool], initial: bool) -> BoolValue: ...

    @overload
    def reduce[V](
        self, func: Callable[[list[V], ItemT], list[V]], initial: list[V]
    ) -> ListValue[V]: ...

    @overload
    def reduce[K, V](
        self, func: Callable[[dict[K, V], ItemT], dict[K, V]], initial: dict[K, V]
    ) -> DictValue[K, V]: ...

    def reduce[R](self, func: Callable[[R, ItemT], R], initial: R) -> object:
        """Reduce sequence to single value.

        Args:
            func: Function (accumulator, element) -> accumulator
            initial: Starting value for accumulator

        Returns:
            Typed value wrapper containing reduced value at execution time

        Example:
            >>> total = list_ref.reduce(lambda acc, x: acc + x, 0).execute(ctx)
        """
        from every_pv.morphisms import ReduceOp

        return typed_value(type(initial), ReduceOp(self, func, initial))

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
        from every_pv.morphisms import FindValueByPredicateOp

        return typed_value(self.item_type, FindValueByPredicateOp(self, predicate))

    def find_index(self, predicate: Callable[[ItemT], bool]) -> IntValue:
        """Find index of first element matching predicate.

        Args:
            predicate: Function returning True for element to find

        Returns:
            IntValue containing index at execution time

        Example:
            >>> idx = list_ref.find_index(lambda x: x > 10).execute(ctx)
        """
        from every_pv.morphisms import FindIndexByPredicateOp

        return IntValue(FindIndexByPredicateOp(self, predicate))

    def index(self, value: ItemT | Sentinel) -> IntValue:
        """Find index of value in sequence.

        Args:
            value: Value to search for

        Returns:
            IntValue containing index at execution time

        Example:
            >>> idx = list_ref.index("apple").execute(ctx)
        """
        from every_pv.morphisms import IndexOfValueOp

        return IntValue(IndexOfValueOp(self, value))

    def count(self, value: ItemT | Sentinel) -> IntValue:
        """Count occurrences of value in sequence.

        Args:
            value: Value to count

        Returns:
            IntValue containing count at execution time

        Example:
            >>> n = list_ref.count("apple").execute(ctx)
        """
        from every_pv.morphisms import CountOfValueOp

        return IntValue(CountOfValueOp(self, value))


class AppendableBase[ItemT]:
    """Implementation base for appending to sequences.

    Implements the Appendable protocol with append() method.
    """

    def append(self, value: ItemT | Sentinel | Term[ItemT | Sentinel]) -> NoneValue:
        """Create an append command.

        Args:
            value: Item to append (literal or Term)

        Returns:
            NoneValue (append returns None after execution)

        Example:
            >>> list_ref.append(42).execute(ctx)
        """
        from every_pv.morphisms import AppendValueCmd

        return NoneValue(AppendValueCmd(self, ensure_term(value)))


class InsertableBase[ItemT]:
    """Implementation base for inserting into sequences.

    Implements the Insertable protocol with insert() method.
    """

    def insert(
        self,
        index: int | Sentinel | Term[int | Sentinel],
        value: ItemT | Sentinel | Term[ItemT | Sentinel],
    ) -> NoneValue:
        """Create an insert command.

        Args:
            index: Position to insert at
            value: Item to insert (literal or Term)

        Returns:
            NoneValue (insert returns None after execution)

        Example:
            >>> list_ref.insert(0, "first").execute(ctx)
        """
        from every_pv.morphisms import InsertAtIndexCmd

        return NoneValue(InsertAtIndexCmd(self, ensure_term(index), ensure_term(value)))


class PoppableBase[ItemT]:
    """Implementation base for popping from sequences.

    Implements the Poppable protocol with pop() method.
    Requires self to have item_type attribute.
    """

    item_type: type[ItemT]

    @overload
    def pop(
        self: PoppableBase[int],
        index: int | Sentinel | Term[int | Sentinel] | None = None,
    ) -> IntValue: ...

    @overload
    def pop(
        self: PoppableBase[str],
        index: int | Sentinel | Term[int | Sentinel] | None = None,
    ) -> StrValue: ...

    @overload
    def pop(
        self: PoppableBase[float],
        index: int | Sentinel | Term[int | Sentinel] | None = None,
    ) -> FloatValue: ...

    @overload
    def pop(
        self: PoppableBase[bool],
        index: int | Sentinel | Term[int | Sentinel] | None = None,
    ) -> BoolValue: ...

    @overload
    def pop[V](
        self: PoppableBase[list[V]],
        index: int | Sentinel | Term[int | Sentinel] | None = None,
    ) -> ListValue[V]: ...

    @overload
    def pop[K, V](
        self: PoppableBase[dict[K, V]],
        index: int | Sentinel | Term[int | Sentinel] | None = None,
    ) -> DictValue[K, V]: ...

    def pop(self, index: int | Sentinel | Term[int | Sentinel] | None = None) -> object:
        """Create a pop command.

        Args:
            index: Position to pop from (default: last)

        Returns:
            Typed value wrapper containing removed item at execution time

        Example:
            >>> last = list_ref.pop().execute(ctx)
            >>> first = list_ref.pop(0).execute(ctx)
        """
        from every_pv.morphisms import PopByIndexCmd

        wrapped_index = ensure_term(index) if index is not None else None
        return typed_value(self.item_type, PopByIndexCmd(self, wrapped_index))
