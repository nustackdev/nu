"""Capability implementation bases for RValue types.

This module provides hierarchical mixin classes that implement value capabilities.
The hierarchy allows fine-grained composition while providing convenient combined bases.

Hierarchy:
    CoreBase                    - Everyone inherits this (ifelse, is_empty, is_nan, is_special)
    ├── Arithmetic Bases
    │   ├── AddableBase         - __add__, __radd__
    │   ├── SubtractableBase    - __sub__, __rsub__
    │   ├── NegatableBase       - __neg__, __pos__, __abs__
    │   ├── AdditiveBase        - Combines Add + Sub + Negatable
    │   ├── MultiplyableBase    - __mul__, __rmul__
    │   ├── DivisibleBase       - __truediv__, __rtruediv__, __floordiv__, __rfloordiv__
    │   ├── ModuloableBase      - __mod__, __rmod__
    │   ├── PowerableBase       - __pow__, __rpow__
    │   ├── MultiplicativeBase  - Combines Multiply + Divide + Modulo + Power
    │   └── NumericBase         - Combines Additive + Multiplicative (full arithmetic)
    ├── Comparison Bases
    │   ├── OrderableBase       - __gt__, __lt__, __ge__, __le__
    │   ├── EqualableBase       - eq(), ne(), is_()
    │   └── ComparisonBase      - Combines Orderable + Equalable
    ├── Logical Bases
    │   ├── AndableBase         - and_()
    │   ├── OrableBase          - or_()
    │   ├── NotableBase         - not_(), bool_()
    │   └── LogicalBase         - Combines all logical ops
    ├── Bitwise Bases
    │   ├── BitwiseAndableBase  - bitand()
    │   ├── BitwiseOrableBase   - bitor()
    │   ├── BitwiseXorableBase  - __xor__, __rxor__
    │   ├── BitwiseNotableBase  - bitnot()
    │   ├── ShiftableBase       - __lshift__, __rshift__ and reverse
    │   └── BitwiseBase         - Combines all bitwise ops
    ├── Collection Bases
    │   ├── LengthableBase      - len_()
    │   ├── IndexableBase       - __getitem__ for int keys
    │   ├── SliceableBase       - __getitem__ for slices, slice_()
    │   ├── ContainableBase     - contains()
    │   ├── IterableBase        - map_(), filter_(), reduce_(), etc.
    │   ├── SequenceBase        - Combines collection ops for sequences
    │   └── MappingBase         - Combines collection ops for mappings
    └── String Bases
        ├── ConcatenableBase    - __add__ for strings
        └── StringBase          - String-specific operations

Usage:
    class MyIntValue(NumericBase, ComparisonBase, BitwiseBase, CoreBase, Literal[int]):
        # Gets full numeric, comparison, and bitwise operations
        pass

    class MyDecimalValue(AdditiveBase, MultiplyableBase, ComparisonBase, CoreBase, Literal):
        # Gets addition, multiplication (no floor div, mod, pow), and comparison
        pass
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .conversion import literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.types import SpecialValue

    from ..term import RValue
    from .primitive_values import BoolValue, IntValue, StrValue, UnknownValue  # noqa: TC004


__all__ = [  # noqa: RUF022
    # Core base (everyone needs)
    "CoreBase",
    # Atomic arithmetic bases
    "AddableBase",
    "SubtractableBase",
    "NegatableBase",
    "MultiplyableBase",
    "DivisibleBase",
    "ModuloableBase",
    "PowerableBase",
    # Combined arithmetic bases
    "AdditiveBase",
    "MultiplicativeBase",
    "NumericBase",
    # Comparison bases
    "OrderableBase",
    "EqualableBase",
    "ComparisonBase",
    # Logical bases
    "AndableBase",
    "OrableBase",
    "NotableBase",
    "LogicalBase",
    # Bitwise bases
    "BitwiseAndableBase",
    "BitwiseOrableBase",
    "BitwiseXorableBase",
    "BitwiseNotableBase",
    "ShiftableBase",
    "BitwiseBase",
    # Collection bases
    "LengthableBase",
    "IndexableBase",
    "SliceableBase",
    "ContainableBase",
    "IterableBase",
    "SequenceBase",
    "MappingBase",
    # String bases
    "ConcatenableBase",
    "StringBase",
]


# =============================================================================
# CORE BASE - EVERYONE INHERITS THIS
# =============================================================================


class CoreBase:
    """Core base that all values should inherit.

    Provides:
    - is_empty(), is_nan(), is_special() - Special value checks
    - ifelse() - Conditional/ternary operation
    - or_default() - Provide default if empty/nan
    """

    def is_empty(self) -> BoolValue:
        """Check if this value is Empty.

        Returns:
            BoolValue-like result
        """
        from ..computations.unary_ops import IsEmptyOp
        from .primitive_values import BoolValue

        return BoolValue(IsEmptyOp(self))

    def is_nan(self) -> BoolValue:
        """Check if this value is NaN.

        Returns:
            BoolValue-like result
        """
        from ..computations.unary_ops import IsNaNOp
        from .primitive_values import BoolValue

        return BoolValue(IsNaNOp(self))

    def is_special(self) -> BoolValue:
        """Check if this value is a special value (Empty, NaN, etc.).

        Returns:
            BoolValue-like result
        """
        return self.is_empty().or_(self.is_nan())

    def not_empty(self) -> BoolValue:
        """Check if this value is not Empty.

        Returns:
            BoolValue result
        """
        return self.is_empty().not_()

    def not_nan(self) -> BoolValue:
        """Check if this value is not NaN.

        Returns:
            BoolValue result
        """
        return self.is_nan().not_()

    def ifelse[ElseT](
        self,
        condition: bool | RValue[bool | SpecialValue],
        otherwise: ElseT | RValue[ElseT | SpecialValue],
    ) -> UnknownValue:
        """Conditional/ternary operation: if condition then self else otherwise.

        Args:
            condition: Condition to evaluate
            otherwise: Value to return if condition is false

        Returns:
            Self if condition is true, otherwise the alternative

        Example:
            >>> price.ifelse(price > 0, default_price)
            >>> name.ifelse(name.not_empty(), "Unknown")
        """
        from ..computations.ternary_ops import ConditionalOp
        from .primitive_values import UnknownValue

        return UnknownValue(ConditionalOp(literal(condition), self, literal(otherwise)))

    def or_default[DefaultT](self, default: DefaultT | RValue[DefaultT]) -> UnknownValue:
        """Return self if not empty/nan, otherwise return default.

        Args:
            default: Default value if self is empty or nan

        Returns:
            Self if valid, default otherwise

        Example:
            >>> value.or_default(0)  # Returns 0 if value is Empty
        """
        return UnknownValue(self.ifelse(self.is_special(), literal(default)))


# =============================================================================
# ATOMIC ARITHMETIC BASES
# =============================================================================


class AddableBase[OperandT, ResultT]:
    """Base for values that support addition."""

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __add__(self, other: OperandT) -> ResultT:
        """Addition: self + other."""
        from ..computations.binary_ops import AddOp

        return cast("ResultT", self._wrap_arithmetic_result(AddOp(self, literal(other))))

    def __radd__(self, other: OperandT) -> ResultT:
        """Right addition: other + self."""
        from ..computations.binary_ops import AddOp

        return cast("ResultT", self._wrap_arithmetic_result(AddOp(literal(other), self)))


class SubtractableBase[OperandT, ResultT]:
    """Base for values that support subtraction."""

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __sub__(self, other: OperandT) -> ResultT:
        """Subtraction: self - other."""
        from ..computations.binary_ops import SubOp

        return cast("ResultT", self._wrap_arithmetic_result(SubOp(self, literal(other))))

    def __rsub__(self, other: OperandT) -> ResultT:
        """Right subtraction: other - self."""
        from ..computations.binary_ops import SubOp

        return cast("ResultT", self._wrap_arithmetic_result(SubOp(literal(other), self)))


class NegatableBase[ResultT]:
    """Base for values that support unary negation, positive, and abs."""

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __neg__(self) -> ResultT:
        """Negation: -self."""
        from ..computations.unary_ops import NegOp

        return cast("ResultT", self._wrap_arithmetic_result(NegOp(self)))

    def __pos__(self) -> ResultT:
        """Positive: +self."""
        from ..computations.unary_ops import PosOp

        return cast("ResultT", self._wrap_arithmetic_result(PosOp(self)))

    def __abs__(self) -> ResultT:
        """Absolute value: abs(self)."""
        from ..computations.unary_ops import AbsOp

        return cast("ResultT", self._wrap_arithmetic_result(AbsOp(self)))


class MultiplyableBase[OperandT, ResultT]:
    """Base for values that support multiplication."""

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __mul__(self, other: OperandT) -> ResultT:
        """Multiplication: self * other."""
        from ..computations.binary_ops import MulOp

        return cast("ResultT", self._wrap_arithmetic_result(MulOp(self, literal(other))))

    def __rmul__(self, other: OperandT) -> ResultT:
        """Right multiplication: other * self."""
        from ..computations.binary_ops import MulOp

        return cast("ResultT", self._wrap_arithmetic_result(MulOp(literal(other), self)))


class DivisibleBase[OperandT, ResultT]:
    """Base for values that support division (true and floor)."""

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __truediv__(self, other: OperandT) -> ResultT:
        """Division: self / other."""
        from ..computations.binary_ops import DivOp

        return cast("ResultT", self._wrap_arithmetic_result(DivOp(self, literal(other))))

    def __rtruediv__(self, other: OperandT) -> ResultT:
        """Right division: other / self."""
        from ..computations.binary_ops import DivOp

        return cast("ResultT", self._wrap_arithmetic_result(DivOp(literal(other), self)))

    def __floordiv__(self, other: OperandT) -> ResultT:
        """Floor division: self // other."""
        from ..computations.binary_ops import FloorDivOp

        return cast("ResultT", self._wrap_arithmetic_result(FloorDivOp(self, literal(other))))

    def __rfloordiv__(self, other: OperandT) -> ResultT:
        """Right floor division: other // self."""
        from ..computations.binary_ops import FloorDivOp

        return cast("ResultT", self._wrap_arithmetic_result(FloorDivOp(literal(other), self)))


class ModuloableBase[OperandT, ResultT]:
    """Base for values that support modulo operation."""

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __mod__(self, other: OperandT) -> ResultT:
        """Modulo: self % other."""
        from ..computations.binary_ops import ModOp

        return cast("ResultT", self._wrap_arithmetic_result(ModOp(self, literal(other))))

    def __rmod__(self, other: OperandT) -> ResultT:
        """Right modulo: other % self."""
        from ..computations.binary_ops import ModOp

        return cast("ResultT", self._wrap_arithmetic_result(ModOp(literal(other), self)))


class PowerableBase[OperandT, ResultT]:
    """Base for values that support exponentiation."""

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __pow__(self, other: OperandT) -> ResultT:
        """Power: self ** other."""
        from ..computations.binary_ops import PowOp

        return cast("ResultT", self._wrap_arithmetic_result(PowOp(self, literal(other))))

    def __rpow__(self, other: OperandT) -> ResultT:
        """Right power: other ** self."""
        from ..computations.binary_ops import PowOp

        return cast("ResultT", self._wrap_arithmetic_result(PowOp(literal(other), self)))


# =============================================================================
# COMBINED ARITHMETIC BASES
# =============================================================================


class AdditiveBase[OperandT, ResultT](
    AddableBase[OperandT, ResultT],
    SubtractableBase[OperandT, ResultT],
    NegatableBase[ResultT],
):
    """Combined base for additive operations: +, -, neg, pos, abs.

    Use this for types like datetime.timedelta that support addition/subtraction
    but not multiplication/division.
    """

    pass


class MultiplicativeBase[OperandT, ResultT](
    MultiplyableBase[OperandT, ResultT],
    DivisibleBase[OperandT, ResultT],
    ModuloableBase[OperandT, ResultT],
    PowerableBase[OperandT, ResultT],
):
    """Combined base for multiplicative operations: *, /, //, %, **.

    Use this for types that support multiplication family operations.
    """

    pass


class NumericBase[OperandT, ResultT](
    AdditiveBase[OperandT, ResultT],
    MultiplicativeBase[OperandT, ResultT],
):
    """Full arithmetic operations: +, -, *, /, //, %, **, neg, pos, abs.

    Use this for int, float, Decimal, Fraction, and similar numeric types.
    """

    pass


# =============================================================================
# COMPARISON BASES
# =============================================================================


class OrderableBase[OperandT]:
    """Base for values that support ordering comparisons: >, <, >=, <=."""

    def __gt__(self, other: OperandT) -> BoolValue:
        """Greater than: self > other."""
        from ..computations.binary_ops import GtOp
        from .primitive_values import BoolValue

        return BoolValue(GtOp(self, literal(other)))

    def __lt__(self, other: OperandT) -> BoolValue:
        """Less than: self < other."""
        from ..computations.binary_ops import LtOp
        from .primitive_values import BoolValue

        return BoolValue(LtOp(self, literal(other)))

    def __ge__(self, other: OperandT) -> BoolValue:
        """Greater than or equal: self >= other."""
        from ..computations.binary_ops import GeOp
        from .primitive_values import BoolValue

        return BoolValue(GeOp(self, literal(other)))

    def __le__(self, other: OperandT) -> BoolValue:
        """Less than or equal: self <= other."""
        from ..computations.binary_ops import LeOp
        from .primitive_values import BoolValue

        return BoolValue(LeOp(self, literal(other)))


class EqualableBase[OperandT]:
    """Base for values that support equality comparison.

    Note: == and != are blocked; use eq() and ne() methods.
    """

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

    def eq(self, other: OperandT) -> BoolValue:
        """Equality: self == other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from ..computations.binary_ops import EqOp
        from .primitive_values import BoolValue

        return BoolValue(EqOp(self, literal(other)))

    def ne(self, other: OperandT) -> BoolValue:
        """Inequality: self != other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from ..computations.binary_ops import NeOp
        from .primitive_values import BoolValue

        return BoolValue(NeOp(self, literal(other)))

    def is_(self, other: object) -> BoolValue:
        """Identity comparison: self is other (safe method).

        Args:
            other: Value to compare id to

        Returns:
            IdCompOp expression
        """
        from ..computations.binary_ops import IdCompOp
        from .primitive_values import BoolValue

        return BoolValue(IdCompOp(self, literal(other)))


class ComparisonBase[OperandT](
    OrderableBase[OperandT],
    EqualableBase[OperandT],
):
    """Full comparison operations: >, <, >=, <=, eq(), ne(), is_().

    Use this for most comparable types.
    """

    pass


# =============================================================================
# LOGICAL BASES
# =============================================================================


class AndableBase[OperandT, ResultT]:
    """Base for values that support logical AND."""

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def and_(self, other: OperandT) -> ResultT:
        """Logical AND: self AND other.

        Args:
            other: Value to AND with

        Returns:
            AND result
        """
        from ..computations.binary_ops import AndOp

        return cast("ResultT", self._wrap_logical_result(AndOp(self, literal(other))))


class OrableBase[OperandT, ResultT]:
    """Base for values that support logical OR."""

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def or_(self, other: OperandT) -> ResultT:
        """Logical OR: self OR other.

        Args:
            other: Value to OR with

        Returns:
            OR result
        """
        from ..computations.binary_ops import OrOp

        return cast("ResultT", self._wrap_logical_result(OrOp(self, literal(other))))


class NotableBase[ResultT]:
    """Base for values that support logical NOT and bool conversion."""

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __bool__(self) -> bool:
        """Bool conversion is blocked in DSL context.

        Raises:
            TypeError: Cannot convert to bool directly
        """
        raise TypeError(
            "Cannot convert RValue to bool directly. Use .bool_() method or explicit comparisons."
        )

    def __and__(self, other: object) -> object:
        """Bitwise AND is blocked; use and_() method."""
        raise TypeError("Cannot use & operator on RValues. Use .and_(other) method instead.")

    def __or__(self, other: object) -> object:
        """Bitwise OR is blocked; use or_() method."""
        raise TypeError("Cannot use | operator on RValues. Use .or_(other) method instead.")

    def not_(self) -> ResultT:
        """Logical NOT: NOT self.

        Returns:
            NOT result
        """
        from ..computations.unary_ops import NotOp

        return cast("ResultT", self._wrap_logical_result(NotOp(self)))

    def bool_(self) -> ResultT:
        """Convert to boolean value.

        Returns:
            Boolean result
        """
        from ..computations.unary_ops import BoolOp

        return cast("ResultT", self._wrap_logical_result(BoolOp(self)))


class LogicalBase[OperandT, ResultT](
    AndableBase[OperandT, ResultT],
    OrableBase[OperandT, ResultT],
    NotableBase[ResultT],
):
    """Full logical operations: and_(), or_(), not_(), bool_().

    Use this for boolean-like types.
    """

    pass


# =============================================================================
# BITWISE BASES
# =============================================================================


class BitwiseAndableBase[OperandT, ResultT]:
    """Base for values that support bitwise AND."""

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def bitand(self, other: OperandT) -> ResultT:
        """Bitwise AND: self & other (safe method).

        Args:
            other: Value to AND with

        Returns:
            AND result
        """
        from ..computations.binary_ops import BitwiseAndOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseAndOp(self, literal(other))))


class BitwiseOrableBase[OperandT, ResultT]:
    """Base for values that support bitwise OR."""

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def bitor(self, other: OperandT) -> ResultT:
        """Bitwise OR: self | other (safe method).

        Args:
            other: Value to OR with

        Returns:
            OR result
        """
        from ..computations.binary_ops import BitwiseOrOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseOrOp(self, literal(other))))


class BitwiseXorableBase[OperandT, ResultT]:
    """Base for values that support bitwise XOR."""

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __xor__(self, other: OperandT) -> ResultT:
        """Bitwise XOR: self ^ other."""
        from ..computations.binary_ops import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(self, literal(other))))

    def __rxor__(self, other: OperandT) -> ResultT:
        """Right XOR: other ^ self."""
        from ..computations.binary_ops import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(literal(other), self)))


class BitwiseNotableBase[ResultT]:
    """Base for values that support bitwise NOT."""

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def bitnot(self) -> ResultT:
        """Bitwise NOT: ~self (safe method).

        Returns:
            Inverted value
        """
        from ..computations.unary_ops import BitwiseNotOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseNotOp(self)))


class ShiftableBase[OperandT, ResultT]:
    """Base for values that support bit shifting."""

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __lshift__(self, other: OperandT) -> ResultT:
        """Left shift: self << other."""
        from ..computations.binary_ops import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(self, literal(other))))

    def __rlshift__(self, other: OperandT) -> ResultT:
        """Right left shift: other << self."""
        from ..computations.binary_ops import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(literal(other), self)))

    def __rshift__(self, other: OperandT) -> ResultT:
        """Right shift: self >> other."""
        from ..computations.binary_ops import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(self, literal(other))))

    def __rrshift__(self, other: OperandT) -> ResultT:
        """Right right shift: other >> self."""
        from ..computations.binary_ops import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(literal(other), self)))


class BitwiseBase[OperandT, ResultT](
    BitwiseAndableBase[OperandT, ResultT],
    BitwiseOrableBase[OperandT, ResultT],
    BitwiseXorableBase[OperandT, ResultT],
    BitwiseNotableBase[ResultT],
    ShiftableBase[OperandT, ResultT],
):
    """Full bitwise operations: bitand(), bitor(), ^, bitnot(), <<, >>.

    Use this for integer types that support bitwise operations.
    """

    pass


# =============================================================================
# COLLECTION BASES
# =============================================================================


class LengthableBase:
    """Base for values that have a length."""

    def len_(self) -> IntValue:
        """Get length of this value.

        Returns:
            Length value
        """
        from ..computations.sequence_ops import LenOp
        from .primitive_values import IntValue

        return IntValue(LenOp(self))


class IndexableBase[KeyT, ResultValue]:
    """Base for values that support index/key access."""

    def _wrap_indexable_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __getitem__(self, key: KeyT) -> ResultValue:
        """Get item at index/key."""
        from ..computations.sequence_ops import AtOp

        return cast("ResultValue", self._wrap_indexable_result(AtOp(self, literal(key))))


class SliceableBase[ResultT]:
    """Base for values that support slicing."""

    def _wrap_sliceable_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def slice_(self, start: int | None, stop: int | None, step: int | None = None) -> ResultT:
        """Get slice of this value.

        Args:
            start: Start index
            stop: Stop index
            step: Step size

        Returns:
            Sliced result
        """
        from ..computations.sequence_ops import SliceOp

        return cast("ResultT", self._wrap_sliceable_result(SliceOp(self, start, stop, step)))


class ContainableBase[ItemT]:
    """Base for values that support containment testing."""

    def contains(self, item: ItemT) -> BoolValue:
        """Check if item is in this value.

        Args:
            item: Item to check

        Returns:
            Boolean result
        """
        from ..computations.mapping_ops import ContainsOp
        from .primitive_values import BoolValue

        return BoolValue(ContainsOp(self, literal(item)))


class IterableBase[ElementT, ResultT]:
    """Base for values that support functional iteration operations."""

    def _wrap_iterable_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate collection type."""
        return operand

    def _wrap_element_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate element type."""
        return operand

    def map_[R](self, func: Callable[[ElementT], R]) -> ResultT:
        """Map function over elements.

        Args:
            func: Function to apply

        Returns:
            Mapped result
        """
        from ..computations.sequence_ops import MapOp

        return cast("ResultT", self._wrap_iterable_result(MapOp(self, func)))

    def filter_(self, predicate: Callable[[ElementT], bool]) -> ResultT:
        """Filter elements by predicate.

        Args:
            predicate: Filter function

        Returns:
            Filtered result
        """
        from ..computations.sequence_ops import FilterOp

        return cast("ResultT", self._wrap_iterable_result(FilterOp(self, predicate)))

    def reduce_[R](self, func: Callable[[R, ElementT], R], initial: R) -> UnknownValue:
        """Reduce to single value.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            Reduced value
        """
        from ..computations.sequence_ops import ReduceOp
        from .primitive_values import UnknownValue

        return UnknownValue(ReduceOp(self, func, initial))

    def sum_(self) -> ResultT:
        """Sum all elements.

        Returns:
            Sum
        """
        from ..computations.sequence_ops import SumOp

        return cast("ResultT", self._wrap_element_result(SumOp(self)))

    def min_(self) -> ResultT:
        """Get minimum element.

        Returns:
            Minimum
        """
        from ..computations.sequence_ops import MinOp

        return cast("ResultT", self._wrap_element_result(MinOp(self)))

    def max_(self) -> ResultT:
        """Get maximum element.

        Returns:
            Maximum
        """
        from ..computations.sequence_ops import MaxOp

        return cast("ResultT", self._wrap_element_result(MaxOp(self)))

    def any_(self) -> BoolValue:
        """Check if any element is truthy.

        Returns:
            Boolean result
        """
        from ..computations.sequence_ops import AnyOp
        from .primitive_values import BoolValue

        return BoolValue(AnyOp(self))

    def all_(self) -> BoolValue:
        """Check if all elements are truthy.

        Returns:
            Boolean result
        """
        from ..computations.sequence_ops import AllOp
        from .primitive_values import BoolValue

        return BoolValue(AllOp(self))


class SequenceBase[ElementT, ResultT](
    LengthableBase,
    SliceableBase[ResultT],
    ContainableBase[ElementT],
    IterableBase[ElementT, ResultT],
):
    """Combined base for sequence-like values.

    Provides: len_(), slice_(), contains(), map_(), filter_(), reduce_(),
    sum_(), min_(), max_(), any_(), all_().

    Subclasses typically also implement __getitem__ for indexing.
    """

    def first(self) -> ResultT:
        """Get first element.

        Returns:
            First element
        """
        from ..computations.sequence_ops import FirstOp

        return cast("ResultT", self._wrap_element_result(FirstOp(self)))

    def last(self) -> ResultT:
        """Get last element.

        Returns:
            Last element
        """
        from ..computations.sequence_ops import LastOp

        return cast("ResultT", self._wrap_element_result(LastOp(self)))

    def reversed_(self) -> ResultT:
        """Get reversed sequence.

        Returns:
            Reversed sequence
        """
        from ..computations.sequence_ops import ReversedOp

        return cast("ResultT", self._wrap_sliceable_result(ReversedOp(self)))

    def sorted_(self, reverse: bool = False) -> ResultT:
        """Get sorted sequence.

        Args:
            reverse: Sort descending

        Returns:
            Sorted sequence
        """
        from ..computations.sequence_ops import SortedOp

        return cast("ResultT", self._wrap_sliceable_result(SortedOp(self, reverse=reverse)))

    def join(self, separator: str) -> StrValue:
        """Join string elements.

        Args:
            separator: Separator string

        Returns:
            Joined string
        """
        from ..computations.sequence_ops import JoinOp
        from .primitive_values import StrValue

        return StrValue(JoinOp(self, literal(separator)))

    def index(self, value: ElementT) -> IntValue:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            Index
        """
        from ..computations.sequence_ops import IndexOfOp
        from .primitive_values import IntValue

        return IntValue(IndexOfOp(self, literal(value)))

    def count(self, value: ElementT) -> IntValue:
        """Count occurrences.

        Args:
            value: Value to count

        Returns:
            Count
        """
        from ..computations.sequence_ops import CountOp
        from .primitive_values import IntValue

        return IntValue(CountOp(self, literal(value)))


class MappingBase[KeyT, ValueT, ResultT](
    LengthableBase,
    ContainableBase[KeyT],
):
    """Combined base for mapping-like values.

    Provides: len_(), contains(), keys_(), values_(), items_(), get_().

    Subclasses typically also implement __getitem__ for key access.
    """

    def _wrap_keys_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap keys sequence result."""
        return operand

    def _wrap_values_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap values sequence result."""
        return operand

    def _wrap_items_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap items sequence result."""
        return operand

    def _wrap_value_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap single value result."""
        return operand

    def keys_(self) -> ResultT:
        """Get all keys.

        Returns:
            Keys sequence
        """
        from ..computations.mapping_ops import DictKeysOp

        return cast("ResultT", self._wrap_keys_result(DictKeysOp(self)))

    def values_(self) -> ResultT:
        """Get all values.

        Returns:
            Values sequence
        """
        from ..computations.mapping_ops import DictValuesOp

        return cast("ResultT", self._wrap_values_result(DictValuesOp(self)))

    def items_(self) -> ResultT:
        """Get all key-value pairs.

        Returns:
            Items sequence
        """
        from ..computations.mapping_ops import DictItemsOp

        return cast("ResultT", self._wrap_items_result(DictItemsOp(self)))

    def get_(self, key: KeyT, default: ValueT | None = None) -> ResultT:
        """Get value with default.

        Args:
            key: Key to get
            default: Default if not found

        Returns:
            Value or default
        """
        from ..computations.mapping_ops import DictGetOp

        return cast(
            "ResultT", self._wrap_value_result(DictGetOp(self, literal(key), literal(default)))
        )


# =============================================================================
# STRING BASES
# =============================================================================


class ConcatenableBase[OperandT, ResultT](AddableBase[OperandT, ResultT]):
    """Base for values that support concatenation via +.

    Same as AddableBase but semantically for string-like concatenation.
    """

    pass


class StringBase[ResultT](
    ConcatenableBase[str, ResultT],
    LengthableBase,
    SliceableBase[ResultT],
    ContainableBase[str],
):
    """Combined base for string-like values.

    Provides: + (concatenation), len_(), slice_(), contains(),
    plus string-specific operations.

    Subclasses typically also implement __getitem__ for indexing.
    """

    pass

    # def upper(self) -> ResultT:
    #     """Convert to uppercase.

    #     Returns:
    #         Uppercase string
    #     """
    #     from ..computations.string_ops import UpperOp

    #     return cast("ResultT", UpperOp(self))

    # def lower(self) -> ResultT:
    #     """Convert to lowercase.

    #     Returns:
    #         Lowercase string
    #     """
    #     from ..computations.string_ops import LowerOp

    #     return cast("ResultT", LowerOp(self))

    # def strip(self) -> ResultT:
    #     """Strip whitespace.

    #     Returns:
    #         Stripped string
    #     """
    #     from ..computations.string_ops import StripOp

    #     return cast("ResultT", StripOp(self))

    # def split(self, separator: str = " ") -> ResultT:
    #     """Split string.

    #     Args:
    #         separator: Separator string

    #     Returns:
    #         List of substrings
    #     """
    #     from ..computations.string_ops import SplitOp

    #     return cast("ResultT", SplitOp(self, literal(separator)))

    # def replace(self, old: str, new: str) -> ResultT:
    #     """Replace substring.

    #     Args:
    #         old: String to replace
    #         new: Replacement string

    #     Returns:
    #         Modified string
    #     """
    #     from ..computations.string_ops import ReplaceOp

    #     return cast("ResultT", ReplaceOp(self, literal(old), literal(new)))

    # def startswith(self, prefix: str) -> ResultT:
    #     """Check if starts with prefix.

    #     Args:
    #         prefix: Prefix to check

    #     Returns:
    #         Boolean result
    #     """
    #     from ..computations.string_ops import StartsWithOp

    #     return cast("ResultT", StartsWithOp(self, literal(prefix)))

    # def endswith(self, suffix: str) -> ResultT:
    #     """Check if ends with suffix.

    #     Args:
    #         suffix: Suffix to check

    #     Returns:
    #         Boolean result
    #     """
    #     from ..computations.string_ops import EndsWithOp

    #     return cast("ResultT", EndsWithOp(self, literal(suffix)))

    # def format_(self, *args: object, **kwargs: object) -> ResultT:
    #     """Format string with arguments.

    #     Args:
    #         *args: Positional arguments
    #         **kwargs: Keyword arguments

    #     Returns:
    #         Formatted string
    #     """
    #     from ..computations.string_ops import FormatOp

    #     return cast(
    #         "ResultT",
    #         FormatOp(
    #             self, *[literal(a) for a in args], **{k: literal(v) for k, v in kwargs.items()}
    #         ),
    #     )
