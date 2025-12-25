"""Collection RValue implementations.

This module provides concrete RValue types for Python collections:
- ListValue: List values
- DictValue: Dictionary values
- TupleValue: Tuple values
- SetValue: Set values

These wrap native Python collections and enable DSL operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, overload

from .base import Literal
from .bases import (
    ComparisonBase,
    MappingBase,
    SequenceBase,
)
from .conversion import literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..term import RValue


__all__ = [
    "DictValue",
    "FrozenSetValue",
    "ListValue",
    "SetValue",
    "TupleValue",
]


# =============================================================================
# LIST VALUE
# =============================================================================


class ListValue[T](
    SequenceBase[T, "ListValue[T]"],
    ComparisonBase[list[T], "BoolValue"],
    Literal[list[T]],
):
    """RValue representing a list.

    Supports indexing, slicing, length, and functional operations
    (map, filter, reduce, etc.).

    Type Parameters:
        T: Type of elements in the list

    Example:
        >>> val = ListValue([1, 2, 3])
        >>> first = val[0]  # Returns IntValue (for list of ints)
        >>> doubled = val.map_(lambda x: x * 2)  # Returns ListValue
        >>> total = val.sum_()  # Returns IntValue/FloatValue
    """

    VALUE_TYPE: ClassVar[type] = list

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def __add__(self, other: list[T] | ListValue[T]) -> ListValue[T]:
        """Concatenate lists."""
        from ..ops.binary_ops import AddOp

        return ListValue(AddOp(self, literal(other)))

    def __radd__(self, other: list[T]) -> ListValue[T]:
        """Right concatenate lists."""
        from ..ops.binary_ops import AddOp

        return ListValue(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> object: ...

    @overload
    def __getitem__(self, key: slice) -> ListValue[T]: ...

    def __getitem__(self, key: int | slice) -> object:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return ListValue(SliceOp(self, key.start, key.stop, key.step))

        from ..ops.sequence_ops import AtOp
        from .conversion import result

        # FIXME: should be unknown value
        return result(type(self._value[0]) if self._value else object, AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get list length.

        Returns:
            IntValue containing length
        """
        from ..ops.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, item: T) -> BoolValue:
        """Check if item is in list.

        Args:
            item: Item to check

        Returns:
            BoolValue result
        """
        from ..ops.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(item)))

    def reversed_(self) -> ListValue[T]:
        """Get reversed list.

        Returns:
            ListValue with reversed elements
        """
        from ..ops.sequence_ops import ReversedOp

        return ListValue(ReversedOp(self))

    def sorted_(self, reverse: bool = False) -> ListValue[T]:
        """Get sorted list.

        Args:
            reverse: Sort descending

        Returns:
            ListValue with sorted elements
        """
        from ..ops.sequence_ops import SortedOp

        return ListValue(SortedOp(self, reverse=reverse))

    def map_[R](self, func: Callable[[T], R]) -> ListValue[R]:
        """Map function over elements.

        Args:
            func: Function to apply

        Returns:
            ListValue with mapped elements
        """
        from ..ops.sequence_ops import MapOp

        return ListValue(MapOp(self, func))

    def filter_(self, predicate: Callable[[T], bool]) -> ListValue[T]:
        """Filter elements.

        Args:
            predicate: Filter function

        Returns:
            ListValue with filtered elements
        """
        from ..ops.sequence_ops import FilterOp

        return ListValue(FilterOp(self, predicate))

    @overload
    def reduce_(self, func: Callable[[int, T], int], initial: int) -> IntValue: ...

    @overload
    def reduce_(self, func: Callable[[float, T], float], initial: float) -> FloatValue: ...

    @overload
    def reduce_(self, func: Callable[[str, T], str], initial: str) -> StrValue: ...

    @overload
    def reduce_(self, func: Callable[[bool, T], bool], initial: bool) -> BoolValue: ...

    @overload
    def reduce_[V](
        self, func: Callable[[list[V], T], list[V]], initial: list[V]
    ) -> ListValue[V]: ...

    @overload
    def reduce_[K, V](
        self, func: Callable[[dict[K, V], T], dict[K, V]], initial: dict[K, V]
    ) -> DictValue[K, V]: ...

    def reduce_[R](self, func: Callable[[R, T], R], initial: R) -> object:
        """Reduce to single value.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            Typed value wrapper containing reduced result
        """
        from ..ops.sequence_ops import ReduceOp
        from .conversion import result

        return result(type(initial), ReduceOp(self, func, initial))

    def sum_(self) -> IntValue | FloatValue:
        """Sum elements.

        Returns:
            IntValue or FloatValue containing sum
        """
        from ..ops.sequence_ops import SumOp

        return IntValue(SumOp(self))

    def any_(self) -> BoolValue:
        """Check if any truthy.

        Returns:
            BoolValue result
        """
        from ..ops.sequence_ops import AnyOp

        return BoolValue(AnyOp(self))

    def all_(self) -> BoolValue:
        """Check if all truthy.

        Returns:
            BoolValue result
        """
        from ..ops.sequence_ops import AllOp

        return BoolValue(AllOp(self))

    def join(self, separator: str) -> StrValue:
        """Join string elements.

        Args:
            separator: Separator string

        Returns:
            StrValue with joined result
        """
        from ..ops.sequence_ops import JoinOp

        return StrValue(JoinOp(self, separator))

    def index(self, value: T) -> IntValue:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            IntValue containing index
        """
        from ..ops.sequence_ops import IndexOfOp

        return IntValue(IndexOfOp(self, literal(value)))

    def count(self, value: T) -> IntValue:
        """Count occurrences.

        Args:
            value: Value to count

        Returns:
            IntValue containing count
        """
        from ..ops.sequence_ops import CountOp

        return IntValue(CountOp(self, literal(value)))

    def find_index(self, predicate: Callable[[T], bool]) -> IntValue:
        """Find index of first match.

        Args:
            predicate: Match function

        Returns:
            IntValue containing index
        """
        from ..ops.sequence_ops import FindIndexOp

        return IntValue(FindIndexOp(self, predicate))


# =============================================================================
# TUPLE VALUE
# =============================================================================


class TupleValue[*Ts](
    ComparisonBase[tuple, "BoolValue"],
    Literal[tuple[*Ts]],
):
    """RValue representing a tuple.

    Supports indexing and length operations.
    Tuples are immutable so no mutation operations.

    Type Parameters:
        *Ts: Types of elements in the tuple

    Example:
        >>> val = TupleValue((1, "hello", 3.14))
        >>> first = val[0]  # Returns typed value
        >>> length = val.len_()  # Returns IntValue
    """

    VALUE_TYPE: ClassVar[type] = tuple

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    @overload
    def __getitem__(self, key: int) -> object: ...

    @overload
    def __getitem__(self, key: slice) -> TupleValue: ...

    def __getitem__(self, key: int | slice) -> object:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return TupleValue(SliceOp(self, key.start, key.stop, key.step))

        from ..ops.sequence_ops import AtOp
        from .conversion import result

        return result(type(self._value[key]) if self._value else object, AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get tuple length.

        Returns:
            IntValue containing length
        """
        from ..ops.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, item: object) -> BoolValue:
        """Check if item is in tuple.

        Args:
            item: Item to check

        Returns:
            BoolValue result
        """
        from ..ops.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(item)))


# =============================================================================
# DICT VALUE
# =============================================================================


class DictValue[K, V](
    MappingBase[K, V, "DictValue[K, V]"],
    ComparisonBase[dict[K, V], "BoolValue"],
    Literal[dict[K, V]],
):
    """RValue representing a dictionary.

    Supports key access, keys/values/items, and functional operations.

    Type Parameters:
        K: Type of keys
        V: Type of values

    Example:
        >>> val = DictValue({"a": 1, "b": 2})
        >>> a_val = val["a"]  # Returns typed value
        >>> all_keys = val.keys_()  # Returns ListValue[K]
        >>> doubled = val.map_values(lambda x: x * 2)  # Returns DictValue
    """

    VALUE_TYPE: ClassVar[type] = dict

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def __getitem__(self, key: K) -> object:
        """Get value for key."""
        from ..ops.sequence_ops import AtOp
        from .conversion import result

        # Get value type from first value if available
        value_type = type(next(iter(self._value.values()))) if self._value else object
        return result(value_type, AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get number of items.

        Returns:
            IntValue containing length
        """
        from ..ops.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, key: K) -> BoolValue:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            BoolValue result
        """
        from ..ops.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(key)))

    def keys_(self) -> ListValue[K]:
        """Get all keys.

        Returns:
            ListValue containing all keys
        """
        from ..ops.mapping_ops import DictKeysOp

        return ListValue(DictKeysOp(self))

    def values_(self) -> ListValue[V]:
        """Get all values.

        Returns:
            ListValue containing all values
        """
        from ..ops.mapping_ops import DictValuesOp

        return ListValue(DictValuesOp(self))

    def items_(self) -> ListValue[tuple[K, V]]:
        """Get all key-value pairs.

        Returns:
            ListValue containing all (key, value) tuples
        """
        from ..ops.mapping_ops import DictItemsOp

        return ListValue(DictItemsOp(self))


# =============================================================================
# SET VALUE
# =============================================================================


class SetValue[T](
    ComparisonBase[set[T], "BoolValue"],
    Literal[set[T]],
):
    """RValue representing a set.

    Supports containment testing, length, and set operations.

    Type Parameters:
        T: Type of elements in the set

    Example:
        >>> val = SetValue({1, 2, 3})
        >>> exists = val.contains(2)  # Returns BoolValue
    """

    VALUE_TYPE: ClassVar[type] = set

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def len_(self) -> IntValue:
        """Get set size.

        Returns:
            IntValue containing length
        """
        from ..ops.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, item: T) -> BoolValue:
        """Check if item is in set.

        Args:
            item: Item to check

        Returns:
            BoolValue result
        """
        from ..ops.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(item)))


# =============================================================================
# FROZENSET VALUE
# =============================================================================


class FrozenSetValue[T](
    ComparisonBase[frozenset[T], "BoolValue"],
    Literal[frozenset[T]],
):
    """RValue representing a frozenset.

    Supports containment testing, length, and set operations.
    Immutable version of SetValue.

    Type Parameters:
        T: Type of elements in the set

    Example:
        >>> val = FrozenSetValue(frozenset({1, 2, 3}))
        >>> exists = val.contains(2)  # Returns BoolValue
    """

    VALUE_TYPE: ClassVar[type] = frozenset

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def len_(self) -> IntValue:
        """Get set size.

        Returns:
            IntValue containing length
        """
        from ..ops.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, item: T) -> BoolValue:
        """Check if item is in set.

        Args:
            item: Item to check

        Returns:
            BoolValue result
        """
        from ..ops.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(item)))


# Import primitive values for use in this module
from .primitive_values import BoolValue, FloatValue, IntValue, StrValue  # noqa: E402
