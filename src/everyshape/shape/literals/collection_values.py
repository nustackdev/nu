"""Collection RValue implementations.

This module provides concrete RValue types for Python collections:
- ListValue: List values
- DictValue: Dictionary values
- TupleValue: Tuple values
- SetValue: Set values

These wrap native Python collections and enable DSL operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from ..context import ContextProtocol
from .base import LiteralBase
from .bases import (
    ComparisonBase,
    MappingBase,
    SequenceBase,
)
from .conversion import literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..ops.mapping_ops import (
        ContainsOp,
        DictGetOp,
        DictItemsOp,
        DictKeysOp,
        DictValuesOp,
    )
    from ..ops.sequence_ops import (
        AllOp,
        AnyOp,
        AtOp,
        CountOp,
        FilterOp,
        FindIndexOp,
        FindOp,
        FirstOp,
        IndexOfOp,
        JoinOp,
        LastOp,
        LenOp,
        MapOp,
        MaxOp,
        MinOp,
        ReduceOp,
        ReversedOp,
        SliceOp,
        SortedOp,
        SumOp,
    )


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


class ListValue[T, ContextT: ContextProtocol](
    SequenceBase[T, "ListValue[T]", ContextT],
    ComparisonBase[list[T], "BoolValue", ContextT],
    LiteralBase[list[T], ContextT],
):
    """RValue representing a list.

    Supports indexing, slicing, length, and functional operations
    (map, filter, reduce, etc.).

    Type Parameters:
        T: Type of elements in the list

    Example:
        >>> val = ListValue([1, 2, 3])
        >>> first = val[0]  # Returns AtOp
        >>> doubled = val.map_(lambda x: x * 2)  # Returns MapOp
        >>> total = val.sum_()  # Returns SumOp
    """

    VALUE_TYPE: ClassVar[type] = list

    def _wrap_result(self, value: object) -> ListValue[T, ContextT]:
        """Wrap result in ListValue."""
        return ListValue(list(value))  # type: ignore[arg-type]

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)

    def __add__(self, other: list[T] | ListValue[T, ContextT]) -> object:
        """Concatenate lists."""
        from ..ops.binary_ops import AddOp

        return AddOp(self, self._get_operand(other))

    def __radd__(self, other: list[T]) -> object:
        """Right concatenate lists."""
        from ..ops.binary_ops import AddOp

        return AddOp(self._get_operand(other), self)

    def __getitem__(self, key: int | slice) -> AtOp[T, ContextT] | SliceOp[T, ContextT]:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return SliceOp(self, key.start, key.stop, key.step)

        from ..ops.sequence_ops import AtOp

        return AtOp(self, self._get_operand(key))

    def len_(self) -> LenOp[ContextT]:
        """Get list length.

        Returns:
            Length operation
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)

    def contains(self, item: T) -> ContainsOp[ContextT]:
        """Check if item is in list.

        Args:
            item: Item to check

        Returns:
            Contains operation
        """
        from ..ops.mapping_ops import ContainsOp

        return ContainsOp(self, self._get_operand(item))

    def first(self) -> FirstOp[T, ContextT]:
        """Get first element.

        Returns:
            First operation
        """
        from ..ops.sequence_ops import FirstOp

        return FirstOp(self)

    def last(self) -> LastOp[T, ContextT]:
        """Get last element.

        Returns:
            Last operation
        """
        from ..ops.sequence_ops import LastOp

        return LastOp(self)

    def reversed_(self) -> ReversedOp[T, ContextT]:
        """Get reversed list.

        Returns:
            Reversed operation
        """
        from ..ops.sequence_ops import ReversedOp

        return ReversedOp(self)

    def sorted_(self, reverse: bool = False) -> SortedOp[T, ContextT]:
        """Get sorted list.

        Args:
            key: Key function
            reverse: Sort descending

        Returns:
            Sorted operation
        """
        from ..ops.sequence_ops import SortedOp

        return SortedOp(self, reverse=reverse)

    def map_[R](self, func: Callable[[T], R]) -> MapOp[T, R, ContextT]:
        """Map function over elements.

        Args:
            func: Function to apply

        Returns:
            Map operation
        """
        from ..ops.sequence_ops import MapOp

        return MapOp(self, func)

    def filter_(self, predicate: Callable[[T], bool]) -> FilterOp[T, ContextT]:
        """Filter elements.

        Args:
            predicate: Filter function

        Returns:
            Filter operation
        """
        from ..ops.sequence_ops import FilterOp

        return FilterOp(self, predicate)

    def reduce_[R](self, func: Callable[[R, T], R], initial: R) -> ReduceOp[T, R, ContextT]:
        """Reduce to single value.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            Reduce operation
        """
        from ..ops.sequence_ops import ReduceOp

        return ReduceOp(self, func, initial)

    def sum_(self) -> SumOp[T, ContextT]:
        """Sum elements.

        Returns:
            Sum operation
        """
        from ..ops.sequence_ops import SumOp

        return SumOp(self)

    def min_(self) -> MinOp[T, ContextT]:
        """Get minimum.

        Returns:
            Min operation
        """
        from ..ops.sequence_ops import MinOp

        return MinOp(self)

    def max_(self) -> MaxOp[T, ContextT]:
        """Get maximum.

        Returns:
            Max operation
        """
        from ..ops.sequence_ops import MaxOp

        return MaxOp(self)

    def any_(self) -> AnyOp[ContextT]:
        """Check if any truthy.

        Returns:
            Any operation
        """
        from ..ops.sequence_ops import AnyOp

        return AnyOp(self)

    def all_(self) -> AllOp[ContextT]:
        """Check if all truthy.

        Returns:
            All operation
        """
        from ..ops.sequence_ops import AllOp

        return AllOp(self)

    def join(self, separator: str) -> JoinOp[ContextT]:
        """Join string elements.

        Args:
            separator: Separator string

        Returns:
            Join operation
        """
        from ..ops.sequence_ops import JoinOp

        return JoinOp(self, separator)

    def index(self, value: T) -> IndexOfOp[T, ContextT]:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            IndexOf operation
        """
        from ..ops.sequence_ops import IndexOfOp

        return IndexOfOp(self, self._get_operand(value))

    def count(self, value: T) -> CountOp[ContextT]:
        """Count occurrences.

        Args:
            value: Value to count

        Returns:
            Count operation
        """
        from ..ops.sequence_ops import CountOp

        return CountOp(self, self._get_operand(value))

    def find(self, predicate: Callable[[T], bool]) -> FindOp[T, ContextT]:
        """Find first matching element.

        Args:
            predicate: Match function

        Returns:
            Find operation
        """
        from ..ops.sequence_ops import FindOp

        return FindOp(self, predicate)

    def find_index(self, predicate: Callable[[T], bool]) -> FindIndexOp[T, ContextT]:
        """Find index of first match.

        Args:
            predicate: Match function

        Returns:
            FindIndex operation
        """
        from ..ops.sequence_ops import FindIndexOp

        return FindIndexOp(self, predicate)


# =============================================================================
# TUPLE VALUE
# =============================================================================


class TupleValue[*Ts, ContextT: ContextProtocol](
    ComparisonBase[tuple, "BoolValue", ContextT],
    LiteralBase[tuple[*Ts], ContextT],
):
    """RValue representing a tuple.

    Supports indexing and length operations.
    Tuples are immutable so no mutation operations.

    Type Parameters:
        *Ts: Types of elements in the tuple

    Example:
        >>> val = TupleValue((1, "hello", 3.14))
        >>> first = val[0]  # Returns AtOp
        >>> length = val.len_()  # Returns LenOp
    """

    VALUE_TYPE: ClassVar[type] = tuple

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)

    def __getitem__(self, key: int | slice) -> object:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return SliceOp(self, key.start, key.stop, key.step)

        from ..ops.sequence_ops import AtOp

        return AtOp(self, self._get_operand(key))

    def len_(self) -> LenOp[ContextT]:
        """Get tuple length.

        Returns:
            Length operation
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)

    def contains(self, item: object) -> ContainsOp[ContextT]:
        """Check if item is in tuple.

        Args:
            item: Item to check

        Returns:
            Contains operation
        """
        from ..ops.mapping_ops import ContainsOp

        return ContainsOp(self, self._get_operand(item))

    def first(self) -> FirstOp[object, ContextT]:
        """Get first element.

        Returns:
            First operation
        """
        from ..ops.sequence_ops import FirstOp

        return FirstOp(self)

    def last(self) -> LastOp[object, ContextT]:
        """Get last element.

        Returns:
            Last operation
        """
        from ..ops.sequence_ops import LastOp

        return LastOp(self)


# =============================================================================
# DICT VALUE
# =============================================================================


class DictValue[K, V, ContextT: ContextProtocol](
    MappingBase[K, V, "DictValue[K, V]", ContextT],
    ComparisonBase[dict[K, V], "BoolValue", ContextT],
    LiteralBase[dict[K, V], ContextT],
):
    """RValue representing a dictionary.

    Supports key access, keys/values/items, and functional operations.

    Type Parameters:
        K: Type of keys
        V: Type of values

    Example:
        >>> val = DictValue({"a": 1, "b": 2})
        >>> a_val = val["a"]  # Returns AtOp
        >>> all_keys = val.keys_()  # Returns DictKeysOp
        >>> doubled = val.map_values(lambda x: x * 2)  # Returns MapValuesOp
    """

    VALUE_TYPE: ClassVar[type] = dict

    def _wrap_result(self, value: object) -> DictValue[K, V, ContextT]:
        """Wrap result in DictValue."""
        return DictValue(dict(value))  # type: ignore[arg-type]

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)

    def __getitem__(self, key: K) -> AtOp[V, ContextT]:
        """Get value for key."""
        from ..ops.sequence_ops import AtOp

        return AtOp(self, self._get_operand(key))

    def len_(self) -> LenOp[ContextT]:
        """Get number of items.

        Returns:
            Length operation
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)

    def contains(self, key: K) -> ContainsOp[ContextT]:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            Contains operation
        """
        from ..ops.mapping_ops import ContainsOp

        return ContainsOp(self, self._get_operand(key))

    def keys_(self) -> DictKeysOp[K, ContextT]:
        """Get all keys.

        Returns:
            Keys operation
        """
        from ..ops.mapping_ops import DictKeysOp

        return DictKeysOp(self)

    def values_(self) -> DictValuesOp[V, ContextT]:
        """Get all values.

        Returns:
            Values operation
        """
        from ..ops.mapping_ops import DictValuesOp

        return DictValuesOp(self)

    def items_(self) -> DictItemsOp[K, V, ContextT]:
        """Get all key-value pairs.

        Returns:
            Items operation
        """
        from ..ops.mapping_ops import DictItemsOp

        return DictItemsOp(self)

    def get_(self, key: K, default: V | None = None) -> DictGetOp[V, ContextT]:
        """Get value with default.

        Args:
            key: Key to get
            default: Default if not found

        Returns:
            Get operation
        """
        from ..ops.mapping_ops import DictGetOp

        return DictGetOp(self, self._get_operand(key), default)


# =============================================================================
# SET VALUE
# =============================================================================


class SetValue[T, ContextT: ContextProtocol](
    ComparisonBase[set[T], "BoolValue", ContextT],
    LiteralBase[set[T], ContextT],
):
    """RValue representing a set.

    Supports containment testing, length, and set operations.

    Type Parameters:
        T: Type of elements in the set

    Example:
        >>> val = SetValue({1, 2, 3})
        >>> exists = val.contains(2)  # Returns ContainsOp
        >>> combined = val.union_(other)  # Returns UnionOp
    """

    VALUE_TYPE: ClassVar[type] = set

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)

    def len_(self) -> LenOp[ContextT]:
        """Get set size.

        Returns:
            Length operation
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)

    def contains(self, item: T) -> ContainsOp[ContextT]:
        """Check if item is in set.

        Args:
            item: Item to check

        Returns:
            Contains operation
        """
        from ..ops.mapping_ops import ContainsOp

        return ContainsOp(self, self._get_operand(item))

    # Set-specific operations would need custom Ops
    # These are interface placeholders


# =============================================================================
# FROZENSET VALUE
# =============================================================================


class FrozenSetValue[T, ContextT: ContextProtocol](
    ComparisonBase[frozenset[T], "BoolValue", ContextT],
    LiteralBase[frozenset[T], ContextT],
):
    """RValue representing a frozenset.

    Supports containment testing, length, and set operations.
    Immutable version of SetValue.

    Type Parameters:
        T: Type of elements in the set

    Example:
        >>> val = FrozenSetValue(frozenset({1, 2, 3}))
        >>> exists = val.contains(2)  # Returns ContainsOp
    """

    VALUE_TYPE: ClassVar[type] = frozenset

    def _get_operand(self, other: object) -> object:
        """Convert operand to RValue if needed."""
        return literal(other)

    def len_(self) -> LenOp[ContextT]:
        """Get set size.

        Returns:
            Length operation
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)

    def contains(self, item: T) -> ContainsOp[ContextT]:
        """Check if item is in set.

        Args:
            item: Item to check

        Returns:
            Contains operation
        """
        from ..ops.mapping_ops import ContainsOp

        return ContainsOp(self, self._get_operand(item))


# Import BoolValue for type annotations
from .primitive_values import BoolValue  # noqa: E402, F401
