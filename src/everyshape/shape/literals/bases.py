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

from abc import abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.shape.context import ContextProtocol


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


class ArithmeticBase[T, R, ContextT: ContextProtocol]:
    """Base for RValues supporting arithmetic operations.

    Provides default implementations for arithmetic operators
    that create appropriate operation RValues.

    Type Parameters:
        T: Type of operands
        R: Type of result RValue
        ContextT: Execution context type

    Example:
        >>> class IntValue(ArithmeticBase[int, "IntValue", Context]):
        ...     pass
        >>> a = IntValue(5)
        >>> b = a + 3  # Creates AddOp
    """

    @abstractmethod
    def _wrap_result(self, value: object) -> R:
        """Wrap a result value in the appropriate RValue type.

        Args:
            value: Raw value to wrap

        Returns:
            Wrapped RValue
        """
        ...

    @abstractmethod
    def _get_operand(self, other: object) -> object:
        """Convert operand to appropriate form for operation.

        Args:
            other: Raw operand value

        Returns:
            Prepared operand
        """
        ...

    def __add__(self, other: T) -> R:
        """Addition: self + other."""
        from ..ops.binary_ops import AddOp

        return AddOp(self, self._get_operand(other))

    def __radd__(self, other: T) -> R:
        """Right addition: other + self."""
        from ..ops.binary_ops import AddOp

        return AddOp(self._get_operand(other), self)

    def __sub__(self, other: T) -> R:
        """Subtraction: self - other."""
        from ..ops.binary_ops import SubOp

        return SubOp(self, self._get_operand(other))

    def __rsub__(self, other: T) -> R:
        """Right subtraction: other - self."""
        from ..ops.binary_ops import SubOp

        return SubOp(self._get_operand(other), self)

    def __mul__(self, other: T) -> R:
        """Multiplication: self * other."""
        from ..ops.binary_ops import MulOp

        return MulOp(self, self._get_operand(other))

    def __rmul__(self, other: T) -> R:
        """Right multiplication: other * self."""
        from ..ops.binary_ops import MulOp

        return MulOp(self._get_operand(other), self)

    def __truediv__(self, other: T) -> R:
        """Division: self / other."""
        from ..ops.binary_ops import DivOp

        return DivOp(self, self._get_operand(other))

    def __rtruediv__(self, other: T) -> R:
        """Right division: other / self."""
        from ..ops.binary_ops import DivOp

        return DivOp(self._get_operand(other), self)

    def __floordiv__(self, other: T) -> R:
        """Floor division: self // other."""
        from ..ops.binary_ops import FloorDivOp

        return FloorDivOp(self, self._get_operand(other))

    def __rfloordiv__(self, other: T) -> R:
        """Right floor division: other // self."""
        from ..ops.binary_ops import FloorDivOp

        return FloorDivOp(self._get_operand(other), self)

    def __mod__(self, other: T) -> R:
        """Modulo: self % other."""
        from ..ops.binary_ops import ModOp

        return ModOp(self, self._get_operand(other))

    def __rmod__(self, other: T) -> R:
        """Right modulo: other % self."""
        from ..ops.binary_ops import ModOp

        return ModOp(self._get_operand(other), self)

    def __pow__(self, other: T) -> R:
        """Power: self ** other."""
        from ..ops.binary_ops import PowOp

        return PowOp(self, self._get_operand(other))

    def __rpow__(self, other: T) -> R:
        """Right power: other ** self."""
        from ..ops.binary_ops import PowOp

        return PowOp(self._get_operand(other), self)

    def __neg__(self) -> R:
        """Negation: -self."""
        from ..ops.unary_ops import NegOp

        return NegOp(self)

    def __pos__(self) -> R:
        """Positive: +self."""
        from ..ops.unary_ops import PosOp

        return PosOp(self)

    def __abs__(self) -> R:
        """Absolute value: abs(self)."""
        from ..ops.unary_ops import AbsOp

        return AbsOp(self)


# =============================================================================
# COMPARISON BASE
# =============================================================================


class ComparisonBase[T, R, ContextT: ContextProtocol]:
    """Base for RValues supporting comparison operations.

    Provides default implementations for comparison operators.
    Note: == and != are blocked; use eq() and ne() methods.

    Type Parameters:
        T: Type of operands
        R: Type of result RValue (typically BoolValue)
        ContextT: Execution context type

    Example:
        >>> class IntValue(ComparisonBase[int, "BoolValue", Context]):
        ...     pass
        >>> a = IntValue(5)
        >>> result = a > 3  # Creates GtOp
    """

    @abstractmethod
    def _get_operand(self, other: object) -> object:
        """Convert operand to appropriate form."""
        ...

    def __gt__(self, other: T) -> R:
        """Greater than: self > other."""
        from ..ops.binary_ops import GtOp

        return GtOp(self, self._get_operand(other))

    def __lt__(self, other: T) -> R:
        """Less than: self < other."""
        from ..ops.binary_ops import LtOp

        return LtOp(self, self._get_operand(other))

    def __ge__(self, other: T) -> R:
        """Greater than or equal: self >= other."""
        from ..ops.binary_ops import GeOp

        return GeOp(self, self._get_operand(other))

    def __le__(self, other: T) -> R:
        """Less than or equal: self <= other."""
        from ..ops.binary_ops import LeOp

        return LeOp(self, self._get_operand(other))

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        """Equality is blocked in DSL context.

        Raises:
            TypeError: Use eq() method instead
        """
        raise TypeError("Cannot use == directly on RValues. Use .eq(other) method instead.")

    def __ne__(self, other: object) -> bool:  # type: ignore[override]
        """Inequality is blocked in DSL context.

        Raises:
            TypeError: Use ne() method instead
        """
        raise TypeError("Cannot use != directly on RValues. Use .ne(other) method instead.")

    def eq(self, other: T) -> R:
        """Equality: self == other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from ..ops.binary_ops import EqOp

        return EqOp(self, self._get_operand(other))

    def ne(self, other: T) -> R:
        """Inequality: self != other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from ..ops.binary_ops import NeOp

        return NeOp(self, self._get_operand(other))


# =============================================================================
# LOGICAL BASE
# =============================================================================


class LogicalBase[T, R, ContextT: ContextProtocol]:
    """Base for RValues supporting logical operations.

    Provides default implementations for logical operators.
    Note: & and | are blocked; use and_() and or_() methods.

    Type Parameters:
        T: Type of operands
        R: Type of result RValue
        ContextT: Execution context type

    Example:
        >>> class BoolValue(LogicalBase[bool, "BoolValue", Context]):
        ...     pass
        >>> a = BoolValue(True)
        >>> result = a.and_(other)  # Creates AndOp
    """

    @abstractmethod
    def _get_operand(self, other: object) -> object:
        """Convert operand to appropriate form."""
        ...

    def __bool__(self) -> bool:
        """Bool conversion is blocked in DSL context.

        Raises:
            TypeError: Cannot convert to bool directly
        """
        raise TypeError(
            "Cannot convert RValue to bool directly. Use .bool_() method or explicit comparisons."
        )

    def __and__(self, other: T) -> R:
        """Bitwise AND is blocked; use and_() method.

        Raises:
            TypeError: Use and_() method instead
        """
        raise TypeError("Cannot use & operator on RValues. Use .and_(other) method instead.")

    def __or__(self, other: T) -> R:
        """Bitwise OR is blocked; use or_() method.

        Raises:
            TypeError: Use or_() method instead
        """
        raise TypeError("Cannot use | operator on RValues. Use .or_(other) method instead.")

    def and_(self, other: T) -> R:
        """Logical AND: self AND other (safe method).

        Args:
            other: Value to AND with

        Returns:
            AND result
        """
        from ..ops.binary_ops import AndOp

        return AndOp(self, self._get_operand(other))

    def or_(self, other: T) -> R:
        """Logical OR: self OR other (safe method).

        Args:
            other: Value to OR with

        Returns:
            OR result
        """
        from ..ops.binary_ops import OrOp

        return OrOp(self, self._get_operand(other))

    def not_(self) -> R:
        """Logical NOT: NOT self (safe method).

        Returns:
            NOT result
        """
        from ..ops.unary_ops import NotOp

        return NotOp(self)

    def bool_(self) -> R:
        """Convert to boolean value.

        Returns:
            Boolean result
        """
        from ..ops.unary_ops import BoolOp

        return BoolOp(self)


# =============================================================================
# BITWISE BASE
# =============================================================================


class BitwiseBase[T, R, ContextT: ContextProtocol]:
    """Base for RValues supporting bitwise operations.

    Provides implementations for bitwise operators.

    Type Parameters:
        T: Type of operands
        R: Type of result RValue
        ContextT: Execution context type

    Example:
        >>> class IntValue(BitwiseBase[int, "IntValue", Context]):
        ...     pass
        >>> a = IntValue(0xFF)
        >>> result = a ^ 0x0F  # Creates XorOp
    """

    @abstractmethod
    def _get_operand(self, other: object) -> object:
        """Convert operand to appropriate form."""
        ...

    def __xor__(self, other: T) -> R:
        """Bitwise XOR: self ^ other."""
        from ..ops.binary_ops import XorOp

        return XorOp(self, self._get_operand(other))

    def __rxor__(self, other: T) -> R:
        """Right XOR: other ^ self."""
        from ..ops.binary_ops import XorOp

        return XorOp(self._get_operand(other), self)

    def __lshift__(self, other: T) -> R:
        """Left shift: self << other."""
        from ..ops.binary_ops import LShiftOp

        return LShiftOp(self, self._get_operand(other))

    def __rlshift__(self, other: T) -> R:
        """Right left shift: other << self."""
        from ..ops.binary_ops import LShiftOp

        return LShiftOp(self._get_operand(other), self)

    def __rshift__(self, other: T) -> R:
        """Right shift: self >> other."""
        from ..ops.binary_ops import RShiftOp

        return RShiftOp(self, self._get_operand(other))

    def __rrshift__(self, other: T) -> R:
        """Right right shift: other >> self."""
        from ..ops.binary_ops import RShiftOp

        return RShiftOp(self._get_operand(other), self)

    def bitnot(self) -> R:
        """Bitwise NOT: ~self (safe method).

        Returns:
            Inverted value
        """
        from ..ops.unary_ops import BitwiseNotOp

        return BitwiseNotOp(self)

    def bitand(self, other: T) -> R:
        """Bitwise AND: self & other (safe method).

        Args:
            other: Value to AND with

        Returns:
            AND result
        """
        # We use a custom op for bitand since & is blocked for logical AND
        from ..ops.binary_ops import BitwiseAndOp

        return BitwiseAndOp(self, self._get_operand(other))

    def bitor(self, other: T) -> R:
        """Bitwise OR: self | other (safe method).

        Args:
            other: Value to OR with

        Returns:
            OR result
        """
        from ..ops.binary_ops import BitwiseOrOp

        return BitwiseOrOp(self, self._get_operand(other))


# =============================================================================
# SEQUENCE BASE
# =============================================================================


class SequenceBase[V, R, ContextT: ContextProtocol]:
    """Base for RValues with sequence-like behavior.

    Provides implementations for sequence operations.

    Type Parameters:
        V: Type of elements
        R: Type of result RValue
        ContextT: Execution context type

    Example:
        >>> class ListValue(SequenceBase[int, "ListValue", Context]):
        ...     pass
        >>> lst = ListValue([1, 2, 3])
        >>> first = lst[0]
    """

    @abstractmethod
    def _get_operand(self, other: object) -> object:
        """Convert operand to appropriate form."""
        ...

    def __getitem__(self, key: int | slice) -> R:
        """Get item or slice."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return SliceOp(self, key.start, key.stop, key.step)

        from ..ops.sequence_ops import AtOp

        return AtOp(self, self._get_operand(key))

    def len_(self) -> R:
        """Get length of sequence.

        Returns:
            Length value
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)

    def contains(self, item: V) -> R:
        """Check if item is in sequence.

        Args:
            item: Item to check

        Returns:
            Boolean result
        """
        from ..ops.mapping_ops import ContainsOp

        return ContainsOp(self, self._get_operand(item))

    def slice_(self, start: int | None, stop: int | None, step: int | None = None) -> R:
        """Get slice of sequence.

        Args:
            start: Start index
            stop: Stop index
            step: Step size

        Returns:
            Sliced sequence
        """
        from ..ops.sequence_ops import SliceOp

        return SliceOp(self, start, stop, step)

    def first(self) -> R:
        """Get first element.

        Returns:
            First element
        """
        from ..ops.sequence_ops import FirstOp

        return FirstOp(self)

    def last(self) -> R:
        """Get last element.

        Returns:
            Last element
        """
        from ..ops.sequence_ops import LastOp

        return LastOp(self)

    def reversed_(self) -> R:
        """Get reversed sequence.

        Returns:
            Reversed sequence
        """
        from ..ops.sequence_ops import ReversedOp

        return ReversedOp(self)

    def sorted_(self, reverse: bool = False) -> R:
        """Get sorted sequence.

        Args:
            key: Key function
            reverse: Sort descending

        Returns:
            Sorted sequence
        """
        from ..ops.sequence_ops import SortedOp

        return SortedOp(self, reverse=reverse)

    def map_[T](self, func: Callable[[V], T]) -> R:
        """Apply function to each element.

        Args:
            func: Function to apply

        Returns:
            Mapped sequence
        """
        from ..ops.sequence_ops import MapOp

        return MapOp(self, func)

    def filter_(self, predicate: Callable[[V], bool]) -> R:
        """Filter elements by predicate.

        Args:
            predicate: Filter function

        Returns:
            Filtered sequence
        """
        from ..ops.sequence_ops import FilterOp

        return FilterOp(self, predicate)

    def reduce_[T](self, func: Callable[[T, V], T], initial: T) -> R:
        """Reduce sequence to single value.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            Reduced value
        """
        from ..ops.sequence_ops import ReduceOp

        return ReduceOp(self, func, initial)

    def sum_(self) -> R:
        """Sum all elements.

        Returns:
            Sum
        """
        from ..ops.sequence_ops import SumOp

        return SumOp(self)

    def min_(self) -> R:
        """Get minimum element.

        Returns:
            Minimum
        """
        from ..ops.sequence_ops import MinOp

        return MinOp(self)

    def max_(self) -> R:
        """Get maximum element.

        Returns:
            Maximum
        """
        from ..ops.sequence_ops import MaxOp

        return MaxOp(self)

    def any_(self) -> R:
        """Check if any element is truthy.

        Returns:
            Boolean result
        """
        from ..ops.sequence_ops import AnyOp

        return AnyOp(self)

    def all_(self) -> R:
        """Check if all elements are truthy.

        Returns:
            Boolean result
        """
        from ..ops.sequence_ops import AllOp

        return AllOp(self)

    def join(self, separator: str) -> R:
        """Join string elements.

        Args:
            separator: Separator string

        Returns:
            Joined string
        """
        from ..ops.sequence_ops import JoinOp

        return JoinOp(self, separator)

    def index(self, value: V) -> R:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            Index
        """
        from ..ops.sequence_ops import IndexOfOp

        return IndexOfOp(self, self._get_operand(value))

    def count(self, value: V) -> R:
        """Count occurrences of value.

        Args:
            value: Value to count

        Returns:
            Count
        """
        from ..ops.sequence_ops import CountOp

        return CountOp(self, self._get_operand(value))


# =============================================================================
# MAPPING BASE
# =============================================================================


class MappingBase[K, V, R, ContextT: ContextProtocol]:
    """Base for RValues with mapping-like behavior.

    Provides implementations for mapping operations.

    Type Parameters:
        K: Type of keys
        V: Type of values
        R: Type of result RValue
        ContextT: Execution context type

    Example:
        >>> class DictValue(MappingBase[str, int, "DictValue", Context]):
        ...     pass
        >>> dct = DictValue({"a": 1})
        >>> val = dct["a"]
    """

    @abstractmethod
    def _get_operand(self, other: object) -> object:
        """Convert operand to appropriate form."""
        ...

    def __getitem__(self, key: K) -> R:
        """Get value for key."""
        from ..ops.sequence_ops import AtOp

        return AtOp(self, self._get_operand(key))

    def len_(self) -> R:
        """Get number of items.

        Returns:
            Length value
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)

    def contains(self, key: K) -> R:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            Boolean result
        """
        from ..ops.mapping_ops import ContainsOp

        return ContainsOp(self, self._get_operand(key))

    def keys_(self) -> R:
        """Get all keys.

        Returns:
            Keys sequence
        """
        from ..ops.mapping_ops import DictKeysOp

        return DictKeysOp(self)

    def values_(self) -> R:
        """Get all values.

        Returns:
            Values sequence
        """
        from ..ops.mapping_ops import DictValuesOp

        return DictValuesOp(self)

    def items_(self) -> R:
        """Get all key-value pairs.

        Returns:
            Items sequence
        """
        from ..ops.mapping_ops import DictItemsOp

        return DictItemsOp(self)

    def get_(self, key: K, default: V | None = None) -> R:
        """Get value with default.

        Args:
            key: Key to get
            default: Default if not found

        Returns:
            Value or default
        """
        from ..ops.mapping_ops import DictGetOp

        return DictGetOp(self, self._get_operand(key), default)


# =============================================================================
# STRING BASE
# =============================================================================


class StringBase[R, ContextT: ContextProtocol]:
    """Base for RValues with string-like behavior.

    Provides implementations for string operations.

    Type Parameters:
        R: Type of result RValue
        ContextT: Execution context type

    Example:
        >>> class StrValue(StringBase["StrValue", Context]):
        ...     pass
        >>> s = StrValue("hello")
        >>> upper = s.upper()
    """

    @abstractmethod
    def _get_operand(self, other: object) -> object:
        """Convert operand to appropriate form."""
        ...

    @abstractmethod
    def _wrap_result(self, value: object) -> R:
        """Wrap result in appropriate RValue."""
        ...

    def __add__(self, other: str) -> R:
        """Concatenate strings."""
        from ..ops.binary_ops import AddOp

        return AddOp(self, self._get_operand(other))

    def __radd__(self, other: str) -> R:
        """Right concatenate strings."""
        from ..ops.binary_ops import AddOp

        return AddOp(self._get_operand(other), self)

    def __getitem__(self, key: int | slice) -> R:
        """Get character or substring."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return SliceOp(self, key.start, key.stop, key.step)

        from ..ops.sequence_ops import AtOp

        return AtOp(self, self._get_operand(key))

    def len_(self) -> R:
        """Get string length.

        Returns:
            Length value
        """
        from ..ops.sequence_ops import LenOp

        return LenOp(self)

    def contains(self, substring: str) -> R:
        """Check if contains substring.

        Args:
            substring: Substring to find

        Returns:
            Boolean result
        """
        from ..ops.mapping_ops import ContainsOp

        return ContainsOp(self, self._get_operand(substring))

    # String-specific methods would need custom Ops
    # These are placeholders for the interface
    # Actual implementations would define StringUpperOp, etc.
