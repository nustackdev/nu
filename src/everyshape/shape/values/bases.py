"""Reusable behavior bases for RValue implementations.

This module provides mixin classes that encapsulate common RValue patterns:
- ArithmeticBase: +, -, *, /, //, %, **
- ComparisonBase: >, <, >=, <=, eq, ne
- LogicalBase: and_, or_, not_
- BitwiseBase: bitand, bitor, ^, ~, <<, >>
- SequenceBase: indexing, slicing, length, iteration ops
- MappingBase: key access, keys, values, items
- StringBase: string-specific operations

These bases use composition to build complete RValue types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .base import Literal
from .conversion import literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..term import RValue


__all__ = [
    "ArithmeticBase",
    "BitwiseBase",
    "ComparisonBase",
    "LogicalBase",
    "MappingBase",
    "SequenceBase",
    "StringBase",
]


# =============================================================================
# ARITHMETIC BASE
# =============================================================================


class ArithmeticBase[OperandT, ReturnLiteralT: Literal]:
    """Base for RValues supporting arithmetic operations.

    Provides default implementations for arithmetic operators
    that create appropriate operation RValues.

    Type Parameters:
        OperandT: Type of operands
        ReturnLiteralT: Type of result value wrapped in Literal to expose right ergonomics
        ContextT: Execution context type

    Example:
        >>> class IntValue(ArithmeticBase[int, "IntValue", Context]):
        ...     pass
        >>> a = IntValue(5)
        >>> b = a + 3  # Creates AddOp
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue: ...

    def __add__(self, other: OperandT) -> ReturnLiteralT:
        """Addition: self + other."""
        from ..ops.binary_ops import AddOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(AddOp(self, literal(other))))

    def __radd__(self, other: OperandT) -> ReturnLiteralT:
        """Right addition: other + self."""
        from ..ops.binary_ops import AddOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(AddOp(literal(other), self)))

    def __sub__(self, other: OperandT) -> ReturnLiteralT:
        """Subtraction: self - other."""
        from ..ops.binary_ops import SubOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(SubOp(self, literal(other))))

    def __rsub__(self, other: OperandT) -> ReturnLiteralT:
        """Right subtraction: other - self."""
        from ..ops.binary_ops import SubOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(SubOp(literal(other), self)))

    def __mul__(self, other: OperandT) -> ReturnLiteralT:
        """Multiplication: self * other."""
        from ..ops.binary_ops import MulOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(MulOp(self, literal(other))))

    def __rmul__(self, other: OperandT) -> ReturnLiteralT:
        """Right multiplication: other * self."""
        from ..ops.binary_ops import MulOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(MulOp(literal(other), self)))

    def __truediv__(self, other: OperandT) -> ReturnLiteralT:
        """Division: self / other."""
        from ..ops.binary_ops import DivOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(DivOp(self, literal(other))))

    def __rtruediv__(self, other: OperandT) -> ReturnLiteralT:
        """Right division: other / self."""
        from ..ops.binary_ops import DivOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(DivOp(literal(other), self)))

    def __floordiv__(self, other: OperandT) -> ReturnLiteralT:
        """Floor division: self // other."""
        from ..ops.binary_ops import FloorDivOp

        return cast(
            "ReturnLiteralT", self._wrap_arithmetic_result(FloorDivOp(self, literal(other)))
        )

    def __rfloordiv__(self, other: OperandT) -> ReturnLiteralT:
        """Right floor division: other // self."""
        from ..ops.binary_ops import FloorDivOp

        return cast(
            "ReturnLiteralT", self._wrap_arithmetic_result(FloorDivOp(literal(other), self))
        )

    def __mod__(self, other: OperandT) -> ReturnLiteralT:
        """Modulo: self % other."""
        from ..ops.binary_ops import ModOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(ModOp(self, literal(other))))

    def __rmod__(self, other: OperandT) -> ReturnLiteralT:
        """Right modulo: other % self."""
        from ..ops.binary_ops import ModOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(ModOp(literal(other), self)))

    def __pow__(self, other: OperandT) -> ReturnLiteralT:
        """Power: self ** other."""
        from ..ops.binary_ops import PowOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(PowOp(self, literal(other))))

    def __rpow__(self, other: OperandT) -> ReturnLiteralT:
        """Right power: other ** self."""
        from ..ops.binary_ops import PowOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(PowOp(literal(other), self)))

    def __neg__(self) -> ReturnLiteralT:
        """Negation: -self."""
        from ..ops.unary_ops import NegOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(NegOp(self)))

    def __pos__(self) -> ReturnLiteralT:
        """Positive: +self."""
        from ..ops.unary_ops import PosOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(PosOp(self)))

    def __abs__(self) -> ReturnLiteralT:
        """Absolute value: abs(self)."""
        from ..ops.unary_ops import AbsOp

        return cast("ReturnLiteralT", self._wrap_arithmetic_result(AbsOp(self)))


# =============================================================================
# COMPARISON BASE
# =============================================================================


class ComparisonBase[OperandT, ReturnLiteralT: Literal]:
    """Base for RValues supporting comparison operations.

    Provides default implementations for comparison operators.
    Note: == and != are blocked; use eq() and ne() methods.

    Type Parameters:
        OperandT: Type of operands
        ReturnLiteralT: Type of result value wrapped in Literal (typically BoolValue)
        ContextT: Execution context type

    Example:
        >>> class IntValue(ComparisonBase[int, "BoolValue", Context]):
        ...     pass
        >>> a = IntValue(5)
        >>> result = a > 3  # Creates GtOp
    """

    def _wrap_comparison_result(self, operand: RValue) -> RValue: ...

    def __gt__(self, other: OperandT) -> ReturnLiteralT:
        """Greater than: self > other."""
        from ..ops.binary_ops import GtOp

        return cast("ReturnLiteralT", self._wrap_comparison_result(GtOp(self, literal(other))))

    def __lt__(self, other: OperandT) -> ReturnLiteralT:
        """Less than: self < other."""
        from ..ops.binary_ops import LtOp

        return cast("ReturnLiteralT", self._wrap_comparison_result(LtOp(self, literal(other))))

    def __ge__(self, other: OperandT) -> ReturnLiteralT:
        """Greater than or equal: self >= other."""
        from ..ops.binary_ops import GeOp

        return cast("ReturnLiteralT", self._wrap_comparison_result(GeOp(self, literal(other))))

    def __le__(self, other: OperandT) -> ReturnLiteralT:
        """Less than or equal: self <= other."""
        from ..ops.binary_ops import LeOp

        return cast("ReturnLiteralT", self._wrap_comparison_result(LeOp(self, literal(other))))

    def __eq__(self, other: object) -> bool:
        """Equality is blocked in DSL context.

        Raises:
            TypeError: Use eq() method instead
        """
        raise TypeError("Cannot use == directly on RValues. Use .eq(other) method instead.")

    def __ne__(self, other: object) -> bool:
        """Inequality is blocked in DSL context.

        Raises:
            TypeError: Use ne() method instead
        """
        raise TypeError("Cannot use != directly on RValues. Use .ne(other) method instead.")

    def eq(self, other: OperandT) -> ReturnLiteralT:
        """Equality: self == other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from ..ops.binary_ops import EqOp

        return cast("ReturnLiteralT", self._wrap_comparison_result(EqOp(self, literal(other))))

    def ne(self, other: OperandT) -> ReturnLiteralT:
        """Inequality: self != other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from ..ops.binary_ops import NeOp

        return cast("ReturnLiteralT", self._wrap_comparison_result(NeOp(self, literal(other))))

    def is_(self, other: object) -> ReturnLiteralT:
        """Identity comparison: self is other (safe method).

        Args:
            other: Value to compare id to (RValue or literal)

        Returns:
            IdCompOp expression
        """
        from ..ops.binary_ops import IdCompOp

        return cast("ReturnLiteralT", self._wrap_comparison_result(IdCompOp(self, literal(other))))

    def bool_(self) -> ReturnLiteralT:
        """Bool vonersion: bool(self).

        Returns:
            BoolOp expression
        """
        from ..ops.unary_ops import BoolOp

        return cast("ReturnLiteralT", BoolOp(self))

    # Convenience methods for working with special values

    def is_empty(self) -> ReturnLiteralT:
        """Check if object is Empty.

        Returns:
            IsEmptyOp expression
        """
        from ..ops.unary_ops import IsEmptyOp

        return cast("ReturnLiteralT", IsEmptyOp(self))

    def not_empty(self) -> ReturnLiteralT:
        """Check if object is not Empty.

        Returns:
            NotEmptyOp expression
        """
        from ..ops.unary_ops import NotEmptyOp

        return cast("ReturnLiteralT", NotEmptyOp(self))

    def is_nan(self) -> ReturnLiteralT:
        """Check if object is NaN.

        Returns:
            IsNaNOp expression
        """
        from ..ops.unary_ops import IsNaNOp

        return cast("ReturnLiteralT", IsNaNOp(self))

    def not_nan(self) -> ReturnLiteralT:
        """Check if object is not NaN.

        Returns:
            NotNaNOp expression
        """
        from ..ops.unary_ops import NotNaNOp

        return cast("ReturnLiteralT", NotNaNOp(self))


# =============================================================================
# LOGICAL BASE
# =============================================================================


class LogicalBase[OperandT, ReturnLiteralT: Literal]:
    """Base for RValues supporting logical operations.

    Provides default implementations for logical operators.
    Note: & and | are blocked; use and_() and or_() methods.

    Type Parameters:
        OperandT: Type of operands
        ReturnLiteralT: Type of result value wrapped in Literal
        ContextT: Execution context type

    Example:
        >>> class BoolValue(LogicalBase[bool, "BoolValue", Context]):
        ...     pass
        >>> a = BoolValue(True)
        >>> result = a.and_(other)  # Creates AndOp
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue: ...

    def __bool__(self) -> bool:
        """Bool conversion is blocked in DSL context.

        Raises:
            TypeError: Cannot convert to bool directly
        """
        raise TypeError(
            "Cannot convert RValue to bool directly. Use .bool_() method or explicit comparisons."
        )

    def __and__(self, other: OperandT) -> ReturnLiteralT:
        """Bitwise AND is blocked; use and_() method.

        Raises:
            TypeError: Use and_() method instead
        """
        raise TypeError("Cannot use & operator on RValues. Use .and_(other) method instead.")

    def __or__(self, other: OperandT) -> ReturnLiteralT:
        """Bitwise OR is blocked; use or_() method.

        Raises:
            TypeError: Use or_() method instead
        """
        raise TypeError("Cannot use | operator on RValues. Use .or_(other) method instead.")

    def and_(self, other: OperandT) -> ReturnLiteralT:
        """Logical AND: self AND other (safe method).

        Args:
            other: Value to AND with

        Returns:
            AND result
        """
        from ..ops.binary_ops import AndOp

        return cast("ReturnLiteralT", self._wrap_logical_result(AndOp(self, literal(other))))

    def or_(self, other: OperandT) -> ReturnLiteralT:
        """Logical OR: self OR other (safe method).

        Args:
            other: Value to OR with

        Returns:
            OR result
        """
        from ..ops.binary_ops import OrOp

        return cast("ReturnLiteralT", self._wrap_logical_result(OrOp(self, literal(other))))

    def not_(self) -> ReturnLiteralT:
        """Logical NOT: NOT self (safe method).

        Returns:
            NOT result
        """
        from ..ops.unary_ops import NotOp

        return cast("ReturnLiteralT", self._wrap_logical_result(NotOp(self)))

    def bool_(self) -> ReturnLiteralT:
        """Convert to boolean value.

        Returns:
            Boolean result
        """
        from ..ops.unary_ops import BoolOp

        return cast("ReturnLiteralT", self._wrap_logical_result(BoolOp(self)))


# =============================================================================
# BITWISE BASE
# =============================================================================


class BitwiseBase[OperandT, ReturnLiteralT: Literal]:
    """Base for RValues supporting bitwise operations.

    Provides implementations for bitwise operators.

    Type Parameters:
        OperandT: Type of operands
        ReturnLiteralT: Type of result value wrapped in Literal
        ContextT: Execution context type

    Example:
        >>> class IntValue(BitwiseBase[int, "IntValue", Context]):
        ...     pass
        >>> a = IntValue(0xFF)
        >>> result = a ^ 0x0F  # Creates XorOp
    """

    def _wrap_bitwise_result(self, operand: RValue) -> RValue: ...

    def __xor__(self, other: OperandT) -> ReturnLiteralT:
        """Bitwise XOR: self ^ other."""
        from ..ops.binary_ops import XorOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(XorOp(self, literal(other))))

    def __rxor__(self, other: OperandT) -> ReturnLiteralT:
        """Right XOR: other ^ self."""
        from ..ops.binary_ops import XorOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(XorOp(literal(other), self)))

    def __lshift__(self, other: OperandT) -> ReturnLiteralT:
        """Left shift: self << other."""
        from ..ops.binary_ops import LShiftOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(LShiftOp(self, literal(other))))

    def __rlshift__(self, other: OperandT) -> ReturnLiteralT:
        """Right left shift: other << self."""
        from ..ops.binary_ops import LShiftOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(LShiftOp(literal(other), self)))

    def __rshift__(self, other: OperandT) -> ReturnLiteralT:
        """Right shift: self >> other."""
        from ..ops.binary_ops import RShiftOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(RShiftOp(self, literal(other))))

    def __rrshift__(self, other: OperandT) -> ReturnLiteralT:
        """Right right shift: other >> self."""
        from ..ops.binary_ops import RShiftOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(RShiftOp(literal(other), self)))

    def bitnot(self) -> ReturnLiteralT:
        """Bitwise NOT: ~self (safe method).

        Returns:
            Inverted value
        """
        from ..ops.unary_ops import BitwiseNotOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(BitwiseNotOp(self)))

    def bitand(self, other: OperandT) -> ReturnLiteralT:
        """Bitwise AND: self & other (safe method).

        Args:
            other: Value to AND with

        Returns:
            AND result
        """
        from ..ops.binary_ops import BitwiseAndOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(BitwiseAndOp(self, literal(other))))

    def bitor(self, other: OperandT) -> ReturnLiteralT:
        """Bitwise OR: self | other (safe method).

        Args:
            other: Value to OR with

        Returns:
            OR result
        """
        from ..ops.binary_ops import BitwiseOrOp

        return cast("ReturnLiteralT", self._wrap_bitwise_result(BitwiseOrOp(self, literal(other))))


# =============================================================================
# SEQUENCE BASE
# =============================================================================


class SequenceBase[ElementT, ReturnLiteralT: Literal]:
    """Base for RValues with sequence-like behavior.

    Provides implementations for sequence operations.

    Type Parameters:
        ElementT: Type of elements
        ReturnLiteralT: Type of result value wrapped in Literal
        ContextT: Execution context type

    Example:
        >>> class ListValue(SequenceBase[int, "ListValue", Context]):
        ...     pass
        >>> lst = ListValue([1, 2, 3])
        >>> first = lst[0]
    """

    def __getitem__(self, key: int | slice) -> ReturnLiteralT:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return cast("ReturnLiteralT", literal(SliceOp(self, key.start, key.stop, key.step)))

        from ..ops.sequence_ops import AtOp

        return cast("ReturnLiteralT", literal(AtOp(self, literal(key))))

    def len_(self) -> ReturnLiteralT:
        """Get length of sequence.

        Returns:
            Length value
        """
        from ..ops.sequence_ops import LenOp

        return cast("ReturnLiteralT", literal(LenOp(self)))

    def contains(self, item: ElementT) -> ReturnLiteralT:
        """Check if item is in sequence.

        Args:
            item: Item to check

        Returns:
            Boolean result
        """
        from ..ops.mapping_ops import ContainsOp

        return cast("ReturnLiteralT", literal(ContainsOp(self, literal(item))))

    def slice_(
        self, start: int | None, stop: int | None, step: int | None = None
    ) -> ReturnLiteralT:
        """Get slice of sequence.

        Args:
            start: Start index
            stop: Stop index
            step: Step size

        Returns:
            Sliced sequence
        """
        from ..ops.sequence_ops import SliceOp

        return cast("ReturnLiteralT", literal(SliceOp(self, start, stop, step)))

    def first(self) -> ReturnLiteralT:
        """Get first element.

        Returns:
            First element
        """
        from ..ops.sequence_ops import FirstOp

        return cast("ReturnLiteralT", literal(FirstOp(self)))

    def last(self) -> ReturnLiteralT:
        """Get last element.

        Returns:
            Last element
        """
        from ..ops.sequence_ops import LastOp

        return cast("ReturnLiteralT", literal(LastOp(self)))

    def reversed_(self) -> ReturnLiteralT:
        """Get reversed sequence.

        Returns:
            Reversed sequence
        """
        from ..ops.sequence_ops import ReversedOp

        return cast("ReturnLiteralT", literal(ReversedOp(self)))

    def sorted_(self, reverse: bool = False) -> ReturnLiteralT:
        """Get sorted sequence.

        Args:
            key: Key function
            reverse: Sort descending

        Returns:
            Sorted sequence
        """
        from ..ops.sequence_ops import SortedOp

        return cast("ReturnLiteralT", literal(SortedOp(self, reverse=reverse)))

    def map_[T](self, func: Callable[[ElementT], T]) -> ReturnLiteralT:
        """Apply function to each element.

        Args:
            func: Function to apply

        Returns:
            Mapped sequence
        """
        from ..ops.sequence_ops import MapOp

        return cast("ReturnLiteralT", literal(MapOp(self, func)))

    def filter_(self, predicate: Callable[[ElementT], bool]) -> ReturnLiteralT:
        """Filter elements by predicate.

        Args:
            predicate: Filter function

        Returns:
            Filtered sequence
        """
        from ..ops.sequence_ops import FilterOp

        return cast("ReturnLiteralT", literal(FilterOp(self, predicate)))

    def reduce_[T](self, func: Callable[[T, ElementT], T], initial: T) -> ReturnLiteralT:
        """Reduce sequence to single value.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            Reduced value
        """
        from ..ops.sequence_ops import ReduceOp

        return cast("ReturnLiteralT", literal(ReduceOp(self, func, initial)))

    def sum_(self) -> ReturnLiteralT:
        """Sum all elements.

        Returns:
            Sum
        """
        from ..ops.sequence_ops import SumOp

        return cast("ReturnLiteralT", literal(SumOp(self)))

    def min_(self) -> ReturnLiteralT:
        """Get minimum element.

        Returns:
            Minimum
        """
        from ..ops.sequence_ops import MinOp

        return cast("ReturnLiteralT", literal(MinOp(self)))

    def max_(self) -> ReturnLiteralT:
        """Get maximum element.

        Returns:
            Maximum
        """
        from ..ops.sequence_ops import MaxOp

        return cast("ReturnLiteralT", literal(MaxOp(self)))

    def any_(self) -> ReturnLiteralT:
        """Check if any element is truthy.

        Returns:
            Boolean result
        """
        from ..ops.sequence_ops import AnyOp

        return cast("ReturnLiteralT", literal(AnyOp(self)))

    def all_(self) -> ReturnLiteralT:
        """Check if all elements are truthy.

        Returns:
            Boolean result
        """
        from ..ops.sequence_ops import AllOp

        return cast("ReturnLiteralT", literal(AllOp(self)))

    def join(self, separator: str) -> ReturnLiteralT:
        """Join string elements.

        Args:
            separator: Separator string

        Returns:
            Joined string
        """
        from ..ops.sequence_ops import JoinOp

        return cast("ReturnLiteralT", literal(JoinOp(self, literal(separator))))

    def index(self, value: ElementT) -> ReturnLiteralT:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            Index
        """
        from ..ops.sequence_ops import IndexOfOp

        return cast("ReturnLiteralT", literal(IndexOfOp(self, literal(value))))

    def count(self, value: ElementT) -> ReturnLiteralT:
        """Count occurrences of value.

        Args:
            value: Value to count

        Returns:
            Count
        """
        from ..ops.sequence_ops import CountOp

        return cast("ReturnLiteralT", literal(CountOp(self, literal(value))))


# =============================================================================
# MAPPING BASE
# =============================================================================


class MappingBase[KeyT, ValueT, ReturnLiteralT: Literal]:
    """Base for RValues with mapping-like behavior.

    Provides implementations for mapping operations.

    Type Parameters:
        KeyT: Type of keys
        ValueT: Type of values
        ReturnLiteralT: Type of result value wrapped in Literal
        ContextT: Execution context type

    Example:
        >>> class DictValue(MappingBase[str, int, "DictValue", Context]):
        ...     pass
        >>> dct = DictValue({"a": 1})
        >>> val = dct["a"]
    """

    def __getitem__(self, key: KeyT) -> ReturnLiteralT:
        """Get value for key."""
        from ..ops.sequence_ops import AtOp

        return cast("ReturnLiteralT", literal(AtOp(self, literal(key))))

    def len_(self) -> ReturnLiteralT:
        """Get number of items.

        Returns:
            Length value
        """
        from ..ops.sequence_ops import LenOp

        return cast("ReturnLiteralT", literal(LenOp(self)))

    def contains(self, key: KeyT) -> ReturnLiteralT:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            Boolean result
        """
        from ..ops.mapping_ops import ContainsOp

        return cast("ReturnLiteralT", literal(ContainsOp(self, literal(key))))

    def keys_(self) -> ReturnLiteralT:
        """Get all keys.

        Returns:
            Keys sequence
        """
        from ..ops.mapping_ops import DictKeysOp

        return cast("ReturnLiteralT", literal(DictKeysOp(self)))

    def values_(self) -> ReturnLiteralT:
        """Get all values.

        Returns:
            Values sequence
        """
        from ..ops.mapping_ops import DictValuesOp

        return cast("ReturnLiteralT", literal(DictValuesOp(self)))

    def items_(self) -> ReturnLiteralT:
        """Get all key-value pairs.

        Returns:
            Items sequence
        """
        from ..ops.mapping_ops import DictItemsOp

        return cast("ReturnLiteralT", literal(DictItemsOp(self)))

    def get_(self, key: KeyT, default: ValueT | None = None) -> ReturnLiteralT:
        """Get value with default.

        Args:
            key: Key to get
            default: Default if not found

        Returns:
            Value or default
        """
        from ..ops.mapping_ops import DictGetOp

        return cast("ReturnLiteralT", literal(DictGetOp(self, literal(key), literal(default))))


# =============================================================================
# STRING BASE
# =============================================================================


class StringBase[ReturnLiteralT: Literal]:
    """Base for RValues with string-like behavior.

    Provides implementations for string operations.

    Type Parameters:
        ReturnLiteralT: Type of result value wrapped in Literal
        ContextT: Execution context type

    Example:
        >>> class StrValue(StringBase["StrValue", Context]):
        ...     pass
        >>> s = StrValue("hello")
        >>> upper = s.upper()
    """
