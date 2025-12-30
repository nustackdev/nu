"""Collection RValue implementations.

This module provides concrete RValue types for Python collections:
- ListValue: List values
- DictValue: Dictionary values
- TupleValue: Tuple values
- SetValue: Set values
- FrozenSetValue: Frozenset values

These wrap native Python collections and enable DSL operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, overload

from everyshape.types import SpecialValue

from ..term import ComputedValue, RValue
from .bases import (
    ComparisonBase,
    CoreBase,
    LengthableBase,
    MappingBase,
    SequenceBase,
    SetBase,
    SliceableBase,
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
    ComparisonBase[list[T]],
    CoreBase,
    ComputedValue[list[T] | SpecialValue],
):
    """RValue representing a list.

    Supports indexing, slicing, length, and functional operations
    (map, filter, reduce, etc.).

    Type Parameters:
        T: Type of elements in the list

    Example:
        >>> val = ListValue([1, 2, 3])
        >>> first = val[0]  # Returns typed value
        >>> doubled = val.map_(lambda x: x * 2)  # Returns ListValue
        >>> total = val.sum_()  # Returns IntValue/FloatValue
    """

    VALUE_TYPE: ClassVar[type] = list

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def __add__(self, other: list[T] | ListValue[T]) -> ListValue[T]:
        """Concatenate lists."""
        from ..computations.binary_ops import AddOp

        return ListValue(AddOp(self, literal(other)))

    def __radd__(self, other: list[T]) -> ListValue[T]:
        """Right concatenate lists."""
        from ..computations.binary_ops import AddOp

        return ListValue(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> UnknownValue: ...

    @overload
    def __getitem__(self, key: slice) -> ListValue[T]: ...

    def __getitem__(self, key: int | slice) -> UnknownValue | ListValue[T]:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return ListValue(SliceOp(self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp

        return UnknownValue(AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get list length.

        Returns:
            IntValue containing length
        """
        from ..computations.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, item: T) -> BoolValue:
        """Check if item is in list.

        Args:
            item: Item to check

        Returns:
            BoolValue result
        """
        from ..computations.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(item)))

    def reversed_(self) -> ListValue[T]:
        """Get reversed list.

        Returns:
            ListValue with reversed elements
        """
        from ..computations.sequence_ops import ReversedOp

        return ListValue(ReversedOp(self))

    def sorted_(self, reverse: bool = False) -> ListValue[T]:
        """Get sorted list.

        Args:
            reverse: Sort descending

        Returns:
            ListValue with sorted elements
        """
        from ..computations.sequence_ops import SortedOp

        return ListValue(SortedOp(self, reverse=reverse))

    def map_[R](self, func: Callable[[T], R]) -> ListValue[R]:
        """Map function over elements.

        Args:
            func: Function to apply

        Returns:
            ListValue with mapped elements
        """
        from ..computations.sequence_ops import MapOp

        return ListValue(MapOp(self, func))

    def filter_(self, predicate: Callable[[T], bool]) -> ListValue[T]:
        """Filter elements.

        Args:
            predicate: Filter function

        Returns:
            ListValue with filtered elements
        """
        from ..computations.sequence_ops import FilterOp

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

    def reduce_[R](self, func: Callable[[R, T], R], initial: R) -> UnknownValue:
        """Reduce to single value.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            Typed value wrapper containing reduced result
        """
        from ..computations.sequence_ops import ReduceOp

        return UnknownValue(ReduceOp(self, func, initial))

    def sum_(self) -> IntValue | FloatValue:
        """Sum elements.

        Returns:
            IntValue or FloatValue containing sum
        """
        from ..computations.sequence_ops import SumOp

        return IntValue(SumOp(self))

    def any_(self) -> BoolValue:
        """Check if any truthy.

        Returns:
            BoolValue result
        """
        from ..computations.sequence_ops import AnyOp

        return BoolValue(AnyOp(self))

    def all_(self) -> BoolValue:
        """Check if all truthy.

        Returns:
            BoolValue result
        """
        from ..computations.sequence_ops import AllOp

        return BoolValue(AllOp(self))

    def join(self, separator: str) -> StrValue:
        """Join string elements.

        Args:
            separator: Separator string

        Returns:
            StrValue with joined result
        """
        from ..computations.sequence_ops import JoinOp

        return StrValue(JoinOp(self, separator))

    def first(self) -> UnknownValue:
        """Get first element.

        Returns:
            First element as UnknownValue
        """
        from ..computations.sequence_ops import FirstOp

        return UnknownValue(FirstOp(self))

    def last(self) -> UnknownValue:
        """Get last element.

        Returns:
            Last element as UnknownValue
        """
        from ..computations.sequence_ops import LastOp

        return UnknownValue(LastOp(self))

    def index(self, value: T) -> IntValue:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            IntValue containing index
        """
        from ..computations.sequence_ops import IndexOfOp

        return IntValue(IndexOfOp(self, literal(value)))

    def count(self, value: T) -> IntValue:
        """Count occurrences.

        Args:
            value: Value to count

        Returns:
            IntValue containing count
        """
        from ..computations.sequence_ops import CountOp

        return IntValue(CountOp(self, literal(value)))

    def find_index(self, predicate: Callable[[T], bool]) -> IntValue:
        """Find index of first match.

        Args:
            predicate: Match function

        Returns:
            IntValue containing index
        """
        from ..computations.sequence_ops import FindIndexOp

        return IntValue(FindIndexOp(self, predicate))


# =============================================================================
# TUPLE VALUE
# =============================================================================


class TupleValue[*Ts](
    LengthableBase,
    SliceableBase["TupleValue"],
    ComparisonBase[tuple],
    CoreBase,
    ComputedValue[tuple[*Ts]],
):
    """RValue representing a tuple.

    Supports indexing, length, and containment operations.
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

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_sliceable_result(self, operand: RValue) -> TupleValue:
        return TupleValue(operand)

    @overload
    def __getitem__(self, key: int) -> UnknownValue: ...

    @overload
    def __getitem__(self, key: slice) -> TupleValue: ...

    def __getitem__(self, key: int | slice) -> UnknownValue | TupleValue:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return TupleValue(SliceOp(self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp

        return UnknownValue(AtOp(self, literal(key)))

    def contains(self, item: object) -> BoolValue:
        """Check if item is in tuple.

        Args:
            item: Item to check

        Returns:
            BoolValue result
        """
        from ..computations.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(item)))

    def first(self) -> UnknownValue:
        """Get first element.

        Returns:
            First element as UnknownValue
        """
        from ..computations.sequence_ops import FirstOp

        return UnknownValue(FirstOp(self))

    def last(self) -> UnknownValue:
        """Get last element.

        Returns:
            Last element as UnknownValue
        """
        from ..computations.sequence_ops import LastOp

        return UnknownValue(LastOp(self))

    def index(self, value: object) -> IntValue:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            IntValue containing index
        """
        from ..computations.sequence_ops import IndexOfOp

        return IntValue(IndexOfOp(self, literal(value)))

    def count(self, value: object) -> IntValue:
        """Count occurrences.

        Args:
            value: Value to count

        Returns:
            IntValue containing count
        """
        from ..computations.sequence_ops import CountOp

        return IntValue(CountOp(self, literal(value)))


# =============================================================================
# DICT VALUE
# =============================================================================


class DictValue[K, V](
    MappingBase[K, V, "DictValue[K, V]"],
    ComparisonBase[dict[K, V]],
    CoreBase,
    ComputedValue[dict[K, V]],
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

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def __getitem__(self, key: K) -> UnknownValue:
        """Get value for key."""
        from ..computations.sequence_ops import AtOp

        return UnknownValue(AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get number of items.

        Returns:
            IntValue containing length
        """
        from ..computations.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, key: K) -> BoolValue:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            BoolValue result
        """
        from ..computations.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(key)))

    def keys_(self) -> ListValue[K]:
        """Get all keys.

        Returns:
            ListValue containing all keys
        """
        from ..computations.mapping_ops import DictKeysOp

        return ListValue(DictKeysOp(self))

    def values_(self) -> ListValue[V]:
        """Get all values.

        Returns:
            ListValue containing all values
        """
        from ..computations.mapping_ops import DictValuesOp

        return ListValue(DictValuesOp(self))

    def items_(self) -> ListValue[tuple[K, V]]:
        """Get all key-value pairs.

        Returns:
            ListValue containing all (key, value) tuples
        """
        from ..computations.mapping_ops import DictItemsOp

        return ListValue(DictItemsOp(self))

    def get_(self, key: K, default: V | None = None) -> UnknownValue:
        """Get value with default.

        Args:
            key: Key to get
            default: Default if not found

        Returns:
            Value or default
        """
        from ..computations.mapping_ops import DictGetOp

        return UnknownValue(DictGetOp(self, literal(key), literal(default)))


# =============================================================================
# SET VALUE
# =============================================================================


class SetValue[T](
    SetBase[T, "SetValue[T]"],
    ComparisonBase[set[T]],
    CoreBase,
    ComputedValue[set[T]],
):
    """RValue representing a set.

    Supports containment testing, length, and set operations.

    Type Parameters:
        T: Type of elements in the set

    Example:
        >>> val = SetValue({1, 2, 3})
        >>> exists = val.contains(2)  # Returns BoolValue
        >>> union = val.union({4, 5})  # Returns SetValue
    """

    VALUE_TYPE: ClassVar[type] = set

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_set_result(self, operand: RValue) -> SetValue[T]:
        return SetValue(operand)


# =============================================================================
# FROZENSET VALUE
# =============================================================================


class FrozenSetValue[T](
    SetBase[T, "FrozenSetValue[T]"],
    ComparisonBase[frozenset[T]],
    CoreBase,
    ComputedValue[frozenset[T]],
):
    """RValue representing a frozenset.

    Supports containment testing, length, and set operations.
    Immutable version of SetValue.

    Type Parameters:
        T: Type of elements in the set

    Example:
        >>> val = FrozenSetValue(frozenset({1, 2, 3}))
        >>> exists = val.contains(2)  # Returns BoolValue
        >>> union = val.union(frozenset({4, 5}))  # Returns FrozenSetValue
    """

    VALUE_TYPE: ClassVar[type] = frozenset

    def _wrap_comparison_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> BoolValue:
        return BoolValue(operand)

    def _wrap_set_result(self, operand: RValue) -> FrozenSetValue[T]:
        return FrozenSetValue(operand)


# Import primitive values for use in this module
from .primitive_values import (  # noqa: E402
    BoolValue,
    FloatValue,
    IntValue,
    StrValue,
    UnknownValue,
)
