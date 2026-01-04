"""Sequence (list/tuple) operations for RValue expressions.

This module provides type-safe operations on sequence RValues:

Aggregation: SumOp, MinOp, MaxOp, LenOp
Transformation: SortedOp, ReversedOp, MapOp, FilterOp
Access: FirstOp, LastOp, AtOp, SliceOp
Boolean: AnyOp, AllOp
String: JoinOp
Functional: ReduceOp

Design principles:
1. Atomic classes: one operation = one class
2. Runtime type checking: validate input is sequence at execution
3. Special value propagation: Empty/NaN flow through operations
4. Type safety: preserve generic T for type inference

Usage:
    # Direct instantiation
    SumOp(prices.extract())
    FirstOp(items.extract())

    # Via ergonomics mixin
    prices.extract().sum_()
    items.extract().first()
"""

from __future__ import annotations

from functools import reduce as functools_reduce
from typing import TYPE_CHECKING, cast

from everyshape.types import NAN, SpecialValue

from ...term import Operation


if TYPE_CHECKING:
    from collections.abc import Callable

    from ...context import Context
    from ...term import RValue
    from ...values.bases import UnionBaseType

__all__ = [
    "AllOp",
    "AnyOp",
    "AtOp",
    "CountOp",
    "FilterOp",
    "FindIndexOp",
    "FindOp",
    "FirstOp",
    "IndexOfOp",
    "JoinOp",
    "LastOp",
    "LenOp",
    "MapOp",
    "MaxOp",
    "MinOp",
    "ReduceOp",
    "ReversedOp",
    "SliceOp",
    "SortedOp",
    "SumOp",
]


# =============================================================================
# ABSTRACT SEQUENCE OPERATION
# =============================================================================

type OpArgument = RValue | UnionBaseType


class SequenceOp[ResultT](Operation[ResultT]):
    """Base class for sequence operations.

    Defines execution pattern: evaluate operand → validate sequence →
    apply operation → return result.
    """

    def __init__(self, operand: OpArgument) -> None:
        """Initialize sequence operation.

        Args:
            operand: RValue that should produce a sequence
        """
        self.children = (cast("RValue", operand),)

    def execute(self, context: Context) -> ResultT:
        """Execute sequence operation.

        Args:
            context: Execution context

        Returns:
            Operation result, or NaN/error if operand is not a sequence
        """
        # Evaluate operand
        operand_val = self.children[0].execute(context)

        # Apply operator-specific logic
        return self._apply_op(operand_val)

    def _apply_op(self, operand: object) -> ResultT:
        """Apply the operation to operand.

        Subclasses override with operation-specific logic.

        Args:
            operand: The evaluated sequence

        Returns:
            Operation result or NaN for errors
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r})"


# =============================================================================
# AGGREGATION OPERATIONS
# =============================================================================


class SumOp[ResultT](SequenceOp[ResultT | SpecialValue]):
    """Sum of sequence elements: sum(seq)."""

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"sum_() requires list or tuple, got {type(operand).__name__}")
        try:
            return sum(operand)  # type: ignore
        except TypeError:
            return NAN


class MinOp[ResultT](SequenceOp[ResultT | SpecialValue]):
    """Minimum element: min(seq)."""

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"min_() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return NAN
        try:
            return min(operand)  # type: ignore
        except TypeError:
            return NAN


class MaxOp[ResultT](SequenceOp[ResultT | SpecialValue]):
    """Maximum element: max(seq)."""

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"max_() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return NAN
        try:
            return max(operand)  # type: ignore
        except TypeError:
            return NAN


class LenOp(SequenceOp[int]):
    """Length of sequence or mapping: len(obj)."""

    def _apply_op(self, operand: object) -> int:
        if not isinstance(operand, (list, tuple, dict, set, frozenset, str)):
            raise TypeError(f"len_() requires sized object, got {type(operand).__name__}")
        return len(operand)


# =============================================================================
# TRANSFORMATION OPERATIONS
# =============================================================================


class SortedOp[ResultT](SequenceOp[list[ResultT] | SpecialValue]):
    """Sorted list: sorted(seq, reverse=reverse)."""

    def __init__(self, operand: OpArgument, *, reverse: bool = False) -> None:
        """Init."""
        super().__init__(operand)
        self._reverse = reverse

    def _apply_op(self, operand: object) -> list[ResultT] | SpecialValue:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"sorted_() requires list or tuple, got {type(operand).__name__}")
        try:
            return sorted(operand, reverse=self._reverse)  # type: ignore
        except TypeError:
            return NAN

    def __repr__(self) -> str:
        return f"SortedOp({self.children[0]!r}, reverse={self._reverse})"


class ReversedOp[ResultT](SequenceOp[list[ResultT]]):
    """Reversed list: list(reversed(seq))."""

    def _apply_op(self, operand: object) -> list[ResultT]:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"reversed_() requires list or tuple, got {type(operand).__name__}")
        return list(reversed(operand))  # type: ignore


# =============================================================================
# ACCESS OPERATIONS
# =============================================================================


class FirstOp[ResultT](SequenceOp[ResultT | SpecialValue]):
    """First element: seq[0]."""

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"first() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return NAN
        return operand[0]  # type: ignore


class LastOp[ResultT](SequenceOp[ResultT | SpecialValue]):
    """Last element: seq[-1]."""

    def _apply_op(self, operand: object) -> ResultT | SpecialValue:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"last() requires list or tuple, got {type(operand).__name__}")
        if len(operand) == 0:
            return NAN
        return operand[-1]  # type: ignore


class AtOp[ResultT](Operation[ResultT | SpecialValue]):
    """Subscript access: seq[key] or dict[key]."""

    def __init__(self, operand: OpArgument, key: OpArgument) -> None:
        """Init."""
        self.children = (cast("RValue", operand), cast("RValue", key))

    def execute(self, context: Context) -> ResultT | SpecialValue:
        """Execute."""
        seq_val = self.children[0].execute(context)
        key_val = self.children[1].execute(context)

        if isinstance(seq_val, (list, tuple)):
            if not isinstance(key_val, int):
                raise TypeError(
                    f"at() index must be int for sequence, got {type(key_val).__name__}"
                )
            if key_val < -len(seq_val) or key_val >= len(seq_val):
                return NAN
            return seq_val[key_val]  # type: ignore
        elif isinstance(seq_val, dict):
            if key_val not in seq_val:
                return NAN
            return seq_val[key_val]  # type: ignore
        else:
            try:
                return seq_val[key_val]  # type: ignore
            except TypeError:
                raise TypeError(
                    f"at() requires subscriptable object, got {type(seq_val).__name__}"
                ) from None

    def __repr__(self) -> str:
        return f"AtOp({self.children[0]!r}, {self.children[1]!r})"


class SliceOp[ResultT](SequenceOp[ResultT]):
    """Slice access: seq[start:stop:step]."""

    def __init__(
        self,
        operand: OpArgument,
        start: int | None = None,
        stop: int | None = None,
        step: int | None = None,
    ) -> None:
        """Init."""
        super().__init__(operand)
        self._start = start
        self._stop = stop
        self._step = step

    def _apply_op(self, operand: object) -> ResultT:
        try:
            return operand[self._start : self._stop : self._step]  # type: ignore
        except TypeError:
            raise TypeError(
                "slice() requires subscriptable object, got {type(seq_val).__name__}"
            ) from None

    def __repr__(self) -> str:
        return f"SliceOp({self.children[0]!r}, {self._start}:{self._stop}:{self._step})"


# =============================================================================
# BOOLEAN OPERATIONS
# =============================================================================


class AnyOp(SequenceOp[bool]):
    """Any truthy: any(seq)."""

    def _apply_op(self, operand: object) -> bool:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"any_() requires list or tuple, got {type(operand).__name__}")
        return any(operand)


class AllOp(SequenceOp[bool]):
    """All truthy: all(seq)."""

    def _apply_op(self, operand: object) -> bool:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"all_() requires list or tuple, got {type(operand).__name__}")
        return all(operand)


# =============================================================================
# STRING OPERATIONS
# =============================================================================


class JoinOp(Operation[str | SpecialValue]):
    """Join strings: sep.join(seq)."""

    def __init__(self, operand: OpArgument, sep: OpArgument) -> None:
        """Init."""
        self.children = (cast("RValue", operand), cast("RValue", sep))

    def execute(self, context: Context) -> str | SpecialValue:
        """Execute."""
        seq_val = self.children[0].execute(context)
        sep_val = self.children[1].execute(context)

        if not isinstance(seq_val, (list, tuple)):
            raise TypeError(f"join() requires list or tuple, got {type(seq_val).__name__}")
        if not isinstance(sep_val, str):
            raise TypeError(f"join() separator must be str, got {type(sep_val).__name__}")

        try:
            return sep_val.join(str(x) for x in seq_val)
        except Exception:
            return NAN

    def __repr__(self) -> str:
        return f"JoinOp({self.children[0]!r}, {self.children[1]!r})"


# =============================================================================
# FUNCTIONAL OPERATIONS
# =============================================================================


class MapOp[T, T2](SequenceOp[list[T2]]):
    """Map function over sequence: list(map(fn, seq)).

    Example:
        >>> prices.extract().map_(lambda x: x * 2)
        >>> items.extract().map_(str)
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T], T2]) -> None:
        """Init.

        Args:
            operand: RValue that produces a sequence
            fn: Function to apply to each element
        """
        super().__init__(operand)
        self._fn = fn

    def _apply_op(self, operand: object) -> list[T2]:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"map_() requires list or tuple, got {type(operand).__name__}")
        return list(map(self._fn, operand))

    def __repr__(self) -> str:
        return f"MapOp({self.children[0]!r}, {self._fn!r})"


class FilterOp[T](SequenceOp[list[T]]):
    """Filter sequence by predicate: list(filter(fn, seq)).

    Example:
        >>> prices.extract().filter_(lambda x: x > 100)
        >>> items.extract().filter_(bool)  # remove falsy values
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T], bool]) -> None:
        """Init.

        Args:
            operand: RValue that produces a sequence
            fn: Predicate function - keep element if returns truthy
        """
        super().__init__(operand)
        self._fn = fn

    def _apply_op(self, operand: object) -> list[T]:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"filter_() requires list or tuple, got {type(operand).__name__}")
        return list(filter(self._fn, operand))  # type: ignore

    def __repr__(self) -> str:
        return f"FilterOp({self.children[0]!r}, {self._fn!r})"


class ReduceOp[T, T2](Operation[T2 | SpecialValue]):
    """Reduce sequence to single value: functools.reduce(fn, seq, initial).

    Example:
        >>> prices.extract().reduce_(lambda acc, x: acc + x, 0)
        >>> items.extract().reduce_(lambda acc, x: acc * x, 1)
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T2, T], T2], initial: T2) -> None:
        """Init.

        Args:
            operand: RValue that produces a sequence
            fn: Reducer function (accumulator, element) -> new_accumulator
            initial: Initial accumulator value
        """
        self.children = (cast("RValue", operand),)
        self._fn = fn
        self._initial = initial

    def execute(self, context: Context) -> T2 | SpecialValue:
        """Execute reduce operation."""
        operand_val = self.children[0].execute(context)

        if not isinstance(operand_val, (list, tuple)):
            raise TypeError(f"reduce_() requires list or tuple, got {type(operand_val).__name__}")

        try:
            return functools_reduce(self._fn, operand_val, self._initial)
        except Exception:
            return NAN

    def __repr__(self) -> str:
        return f"ReduceOp({self.children[0]!r}, {self._fn!r}, {self._initial!r})"


# =============================================================================
# SEARCH OPERATIONS
# =============================================================================


class IndexOfOp[T](Operation[int | SpecialValue]):
    """Find index of value in sequence: seq.index(value).

    Returns NaN if value not found (unlike Python which raises ValueError).

    Example:
        >>> items.extract().index_("apple")
    """

    def __init__(self, operand: OpArgument, value: OpArgument) -> None:
        """Init.

        Args:
            operand: RValue that produces a sequence
            value: Value to search for
        """
        self.children = (cast("RValue", operand), cast("RValue", value))

    def execute(self, context: Context) -> int | SpecialValue:
        """Execute index search."""
        seq_val = self.children[0].execute(context)
        value_val = self.children[1].execute(context)

        if not isinstance(seq_val, (list, tuple)):
            raise TypeError(f"index_() requires list or tuple, got {type(seq_val).__name__}")

        try:
            return list(seq_val).index(value_val)
        except ValueError:
            return NAN

    def __repr__(self) -> str:
        return f"IndexOfOp({self.children[0]!r}, {self.children[1]!r})"


class CountOp(Operation[int]):
    """Count occurrences of value in sequence: seq.count(value).

    Example:
        >>> items.extract().count_("apple")
    """

    def __init__(self, operand: OpArgument, value: OpArgument) -> None:
        """Init.

        Args:
            operand: RValue that produces a sequence
            value: Value to count
        """
        self.children = (cast("RValue", operand), cast("RValue", value))

    def execute(self, context: Context) -> int:
        """Execute count."""
        seq_val = self.children[0].execute(context)
        value_val = self.children[1].execute(context)

        if not isinstance(seq_val, (list, tuple)):
            raise TypeError(f"count_() requires list or tuple, got {type(seq_val).__name__}")

        return list(seq_val).count(value_val)

    def __repr__(self) -> str:
        return f"CountOp({self.children[0]!r}, {self.children[1]!r})"


class FindOp[T](SequenceOp[T | SpecialValue]):
    """Find first element matching predicate.

    Returns NaN if no element matches.

    Example:
        >>> items.extract().find(lambda x: x > 100)
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T], bool]) -> None:
        """Init.

        Args:
            operand: RValue that produces a sequence
            fn: Predicate function
        """
        super().__init__(operand)
        self._fn = fn

    def _apply_op(self, operand: object) -> T | SpecialValue:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"find() requires list or tuple, got {type(operand).__name__}")

        for item in operand:
            if self._fn(item):
                return item  # type: ignore
        return NAN

    def __repr__(self) -> str:
        return f"FindOp({self.children[0]!r}, {self._fn!r})"


class FindIndexOp[T](SequenceOp[int | SpecialValue]):
    """Find index of first element matching predicate.

    Returns NaN if no element matches.

    Example:
        >>> items.extract().find_index(lambda x: x > 100)
    """

    def __init__(self, operand: OpArgument, fn: Callable[[T], bool]) -> None:
        """Init.

        Args:
            operand: RValue that produces a sequence
            fn: Predicate function
        """
        super().__init__(operand)
        self._fn = fn

    def _apply_op(self, operand: object) -> int | SpecialValue:
        if not isinstance(operand, (list, tuple)):
            raise TypeError(f"find_index() requires list or tuple, got {type(operand).__name__}")

        for i, item in enumerate(operand):
            if self._fn(item):
                return i
        return NAN

    def __repr__(self) -> str:
        return f"FindIndexOp({self.children[0]!r}, {self._fn!r})"
