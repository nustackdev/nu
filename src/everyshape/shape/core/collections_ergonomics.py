"""Collection operations mixin for RValue expressions.

This mixin provides methods for working with collection types (list, dict).
All methods return new Operation objects for lazy evaluation.

Naming convention: trailing underscore avoids shadowing Python builtins:
- sum_() not sum()
- keys_() not keys()
- len_() not len()

Example:
    >>> prices = State.prices.extract()
    >>> total = prices.sum_().execute(ctx)
    >>> highest = prices.max_().execute(ctx)
    >>> first_three = prices.slice_(0, 3).execute(ctx)

    >>> users = State.users.extract()
    >>> keys = users.keys_().execute(ctx)
    >>> alice = users.get_("alice", {}).execute(ctx)
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..context import ContextProtocol
    from .mapping_ops import (
        ContainsOp,
        DictGetOp,
        DictItemsOp,
        DictKeysOp,
        DictValuesOp,
    )
    from .sequence_ops import (
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


class CollectionsMixin[T, ContextT: ContextProtocol]:
    """Collection operations mixin for RValue expressions.

    Provides methods for working with sequences (list/tuple) and mappings (dict).
    Methods validate types at runtime and raise TypeError if incompatible.

    Sequence operations: sum_, min_, max_, len_, sorted_, reversed_,
                         first, last, any_, all_, join, at, slice_

    Functional operations: map_, filter_, reduce_

    Search operations: index_, count_, find, find_index

    Mapping operations: keys_, values_, items_, get_, contains_
    """

    def _operand(self, other: object) -> object:
        """Convert operand to RValue.

        This method is inherited from ErgonomicsMixin but we need
        it here for compatibility.
        """
        from .literal_value import literal

        return literal(other)

    # =========================================================================
    # SEQUENCE AGGREGATION OPERATIONS
    # =========================================================================

    def sum_(self) -> SumOp[T, ContextT]:
        """Sum of sequence elements: sum(self).

        Example:
            >>> prices.extract().sum_()
        """
        from .sequence_ops import SumOp

        return SumOp(self)

    def min_(self) -> MinOp[T, ContextT]:
        """Minimum element: min(self).

        Example:
            >>> prices.extract().min_()
        """
        from .sequence_ops import MinOp

        return MinOp(self)

    def max_(self) -> MaxOp[T, ContextT]:
        """Maximum element: max(self).

        Example:
            >>> prices.extract().max_()
        """
        from .sequence_ops import MaxOp

        return MaxOp(self)

    def len_(self) -> LenOp[ContextT]:
        """Length of sequence or mapping: len(self).

        Works for list, tuple, dict, set, str.

        Example:
            >>> items.extract().len_()
        """
        from .sequence_ops import LenOp

        return LenOp(self)

    # =========================================================================
    # SEQUENCE TRANSFORMATION OPERATIONS
    # =========================================================================

    def sorted_(self, *, reverse: bool = False) -> SortedOp[T, ContextT]:
        """Sorted list: sorted(self, reverse=reverse).

        Args:
            reverse: If True, sort in descending order

        Example:
            >>> prices.extract().sorted_()
            >>> prices.extract().sorted_(reverse=True)
        """
        from .sequence_ops import SortedOp

        return SortedOp(self, reverse=reverse)

    def reversed_(self) -> ReversedOp[T, ContextT]:
        """Reversed list: list(reversed(self)).

        Example:
            >>> items.extract().reversed_()
        """
        from .sequence_ops import ReversedOp

        return ReversedOp(self)

    # =========================================================================
    # SEQUENCE ACCESS OPERATIONS
    # =========================================================================

    def first(self) -> FirstOp[T, ContextT]:
        """First element: self[0].

        Returns NaN if sequence is empty.

        Example:
            >>> items.extract().first()
        """
        from .sequence_ops import FirstOp

        return FirstOp(self)

    def last(self) -> LastOp[T, ContextT]:
        """Last element: self[-1].

        Returns NaN if sequence is empty.

        Example:
            >>> items.extract().last()
        """
        from .sequence_ops import LastOp

        return LastOp(self)

    def at(self, key: object) -> AtOp[T, ContextT]:
        """Subscript access: self[key].

        For sequences, key should be an int.
        For dicts, key can be any hashable.

        Returns NaN if key not found or index out of range.

        Example:
            >>> items.extract().at(0)
            >>> users.extract().at("alice")
        """
        from .sequence_ops import AtOp

        return AtOp(self, self._operand(key))

    def slice_(
        self, start: int | None = None, stop: int | None = None, step: int | None = None
    ) -> SliceOp[T, ContextT]:
        """Slice access: self[start:stop:step].

        Args:
            start: Start index (default: 0)
            stop: Stop index (default: end)
            step: Step (default: 1)

        Example:
            >>> items.extract().slice_(0, 3)  # first 3
            >>> items.extract().slice_(None, None, 2)  # every other
        """
        from .sequence_ops import SliceOp

        return SliceOp(self, start, stop, step)

    # =========================================================================
    # SEQUENCE BOOLEAN OPERATIONS
    # =========================================================================

    def any_(self) -> AnyOp[ContextT]:
        """Any truthy: any(self).

        Example:
            >>> flags.extract().any_()
        """
        from .sequence_ops import AnyOp

        return AnyOp(self)

    def all_(self) -> AllOp[ContextT]:
        """All truthy: all(self).

        Example:
            >>> validations.extract().all_()
        """
        from .sequence_ops import AllOp

        return AllOp(self)

    # =========================================================================
    # SEQUENCE STRING OPERATIONS
    # =========================================================================

    def join(self, sep: str | object = "") -> JoinOp[ContextT]:
        """Join strings: sep.join(self).

        Elements are converted to str if necessary.

        Args:
            sep: Separator string

        Example:
            >>> names.extract().join(", ")
        """
        from .sequence_ops import JoinOp

        return JoinOp(self, self._operand(sep))

    # =========================================================================
    # FUNCTIONAL OPERATIONS
    # =========================================================================

    def map_(self, fn: Callable[[T], object]) -> MapOp[T, object, ContextT]:
        """Map function over sequence: list(map(fn, self)).

        Args:
            fn: Function to apply to each element

        Example:
            >>> prices.extract().map_(lambda x: x * 2)
            >>> items.extract().map_(str)
        """
        from .sequence_ops import MapOp

        return MapOp(self, fn)

    def filter_(self, fn: Callable[[T], bool]) -> FilterOp[T, ContextT]:
        """Filter sequence by predicate: list(filter(fn, self)).

        Args:
            fn: Predicate function - keep element if returns truthy

        Example:
            >>> prices.extract().filter_(lambda x: x > 100)
            >>> items.extract().filter_(bool)  # remove falsy values
        """
        from .sequence_ops import FilterOp

        return FilterOp(self, fn)

    def reduce_(
        self, fn: Callable[[object, T], object], initial: object
    ) -> ReduceOp[T, object, ContextT]:
        """Reduce sequence to single value: functools.reduce(fn, self, initial).

        Args:
            fn: Reducer function (accumulator, element) -> new_accumulator
            initial: Initial accumulator value

        Example:
            >>> prices.extract().reduce_(lambda acc, x: acc + x, 0)
            >>> items.extract().reduce_(lambda acc, x: acc * x, 1)
        """
        from .sequence_ops import ReduceOp

        return ReduceOp(self, fn, initial)

    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================

    def index_(self, value: object) -> IndexOfOp[T, ContextT]:
        """Find index of value in sequence: self.index(value).

        Returns NaN if value not found (unlike Python which raises ValueError).

        Args:
            value: Value to search for

        Example:
            >>> items.extract().index_("apple")
        """
        from .sequence_ops import IndexOfOp

        return IndexOfOp(self, self._operand(value))

    def count_(self, value: object) -> CountOp[ContextT]:
        """Count occurrences of value in sequence: self.count(value).

        Args:
            value: Value to count

        Example:
            >>> items.extract().count_("apple")
        """
        from .sequence_ops import CountOp

        return CountOp(self, self._operand(value))

    def find(self, fn: Callable[[T], bool]) -> FindOp[T, ContextT]:
        """Find first element matching predicate.

        Returns NaN if no element matches.

        Args:
            fn: Predicate function

        Example:
            >>> items.extract().find(lambda x: x > 100)
        """
        from .sequence_ops import FindOp

        return FindOp(self, fn)

    def find_index(self, fn: Callable[[T], bool]) -> FindIndexOp[T, ContextT]:
        """Find index of first element matching predicate.

        Returns NaN if no element matches.

        Args:
            fn: Predicate function

        Example:
            >>> items.extract().find_index(lambda x: x > 100)
        """
        from .sequence_ops import FindIndexOp

        return FindIndexOp(self, fn)

    # =========================================================================
    # MAPPING OPERATIONS
    # =========================================================================

    def keys_(self) -> DictKeysOp[T, ContextT]:
        """Dict keys: list(self.keys()).

        Example:
            >>> users.extract().keys_()
        """
        from .mapping_ops import DictKeysOp

        return DictKeysOp(self)

    def values_(self) -> DictValuesOp[T, ContextT]:
        """Dict values: list(self.values()).

        Example:
            >>> users.extract().values_()
        """
        from .mapping_ops import DictValuesOp

        return DictValuesOp(self)

    def items_(self) -> DictItemsOp[T, T, ContextT]:
        """Dict items: list(self.items()).

        Example:
            >>> users.extract().items_()
        """
        from .mapping_ops import DictItemsOp

        return DictItemsOp(self)

    def get_(self, key: object, default: object = None) -> DictGetOp[T, ContextT]:
        """Dict get with default: self.get(key, default).

        Args:
            key: Key to look up
            default: Value to return if key not found

        Example:
            >>> users.extract().get_("alice", {})
        """
        from .mapping_ops import DictGetOp

        return DictGetOp(self, self._operand(key), self._operand(default))

    def contains_(self, item: object) -> ContainsOp[ContextT]:
        """Containment check: item in self.

        Works for sequences, dicts (checks keys), sets, and strings.

        Example:
            >>> users.extract().contains_("alice")  # key in dict
            >>> items.extract().contains_(42)  # value in list
        """
        from .mapping_ops import ContainsOp

        return ContainsOp(self, self._operand(item))
