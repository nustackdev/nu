"""Primitive RValue implementations.

This module provides concrete RValue types for Python primitives:
- IntValue: Integer values
- FloatValue: Floating-point values
- BoolValue: Boolean values
- StrValue: String values
- BytesValue: Bytes values
- NoneValue: None value

Special value types:
- UnknownValue: Value of unknown type (can be any type)
- EmptyValue: Represents absence of a value
- NaNValue: Represents not-a-number

These wrap native Python values and enable DSL operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everyshape.types import SpecialValue

from ..term import ComputedValue
from .bases import (
    BitwiseBase,
    ComparisonBase,
    CoreBase,
    LogicalBase,
    NumericBase,
    StringBase,
)
from .conversion import literal


if TYPE_CHECKING:
    from ..term import RValue


__all__ = [
    "BoolValue",
    "BytesValue",
    "EmptyValue",
    "FloatValue",
    "IntValue",
    "NaNValue",
    "NoneValue",
    "StrValue",
    "UnknownValue",
]


# =============================================================================
# INTEGER VALUE
# =============================================================================


class IntValue(
    NumericBase[
        "int | float | FloatValue | IntValue",
        "FloatValue | IntValue",
    ],
    ComparisonBase["int | float | FloatValue | IntValue"],
    LogicalBase["bool | int | BoolValue | IntValue", "BoolValue"],
    BitwiseBase[
        "int | IntValue",
        "IntValue",
    ],
    CoreBase,
    ComputedValue[int | SpecialValue],
):
    """RValue representing an integer.

    Supports full arithmetic, comparison, logical, and bitwise operations.
    Operations return appropriate RValue types.

    Example:
        >>> val = IntValue(42)
        >>> doubled = val * 2  # Returns IntValue
        >>> is_positive = val > 0  # Returns BoolValue
        >>> masked = val.bitand(0xFF)  # Returns IntValue
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return IntValue(operand)

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        return IntValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# FLOAT VALUE
# =============================================================================


class FloatValue(
    NumericBase[
        "int | float | FloatValue | IntValue",
        "FloatValue",
    ],
    ComparisonBase["int | float | FloatValue | IntValue"],
    LogicalBase["bool | float | BoolValue | FloatValue", "BoolValue"],
    CoreBase,
    ComputedValue[float | SpecialValue],
):
    """RValue representing a floating-point number.

    Supports full arithmetic, comparison, and logical operations.
    Does not support bitwise operations.

    Example:
        >>> val = FloatValue(3.14)
        >>> doubled = val * 2  # Returns FloatValue
        >>> is_positive = val > 0  # Returns BoolValue
        >>> safe = val.or_default(0.0)  # Returns FloatValue if not NaN
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return FloatValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# BOOL VALUE
# =============================================================================


class BoolValue(
    LogicalBase["bool | BoolValue", "BoolValue"],
    ComparisonBase["bool | BoolValue"],
    CoreBase,
    ComputedValue[bool | SpecialValue],
):
    """RValue representing a boolean.

    Supports logical operations: and_, or_, not_.

    Example:
        >>> val = BoolValue(True)
        >>> combined = val.and_(other)  # Returns BoolValue
        >>> negated = val.not_()  # Returns BoolValue
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# STRING VALUE
# =============================================================================


class StrValue(
    StringBase["StrValue"],
    ComparisonBase["str | StrValue"],
    LogicalBase["str | StrValue", "BoolValue"],
    CoreBase,
    ComputedValue[str | SpecialValue],
):
    """RValue representing a string.

    Supports concatenation, indexing, slicing, and string operations.

    Example:
        >>> val = StrValue("hello")
        >>> greeting = val + " world"  # Returns StrValue
        >>> first = val[0]  # Returns StrValue
        >>> length = val.len_()  # Returns IntValue
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def __add__(self, other: str | StrValue) -> StrValue:
        """Concatenate strings."""
        from ..computations.binary_ops import AddOp

        return StrValue(AddOp(self, literal(other)))

    def __radd__(self, other: str) -> StrValue:
        """Right concatenate strings."""
        from ..computations.binary_ops import AddOp

        return StrValue(AddOp[str](literal(other), self))

    # def __getitem__(self, key: int | slice) -> StrValue:
    #     """Get character or substring."""
    #     if isinstance(key, slice):
    #         from ..ops.sequence_ops import SliceOp

    #         return StrValue(SliceOp(self, key.start, key.stop, key.step))

    #     from ..ops.sequence_ops import AtOp

    #     return StrValue(AtOp(self, literal(key)))

    # def len_(self) -> IntValue:
    #     """Get string length.

    #     Returns:
    #         Length value
    #     """
    #     from ..computations.base_ops import LenOp

    #     return IntValue(LenOp(self))

    # def contains(self, substring: str | StrValue) -> BoolValue:
    #     """Check if contains substring.

    #     Args:
    #         substring: Substring to find

    #     Returns:
    #         Boolean result
    #     """
    #     from ..ops.mapping_ops import ContainsOp

    #     return BoolValue(ContainsOp(self, literal(substring)))

    # def upper(self) -> StrValue:
    #     """Convert to uppercase."""
    #     from ..ops.string_ops import UpperOp

    #     return StrValue(UpperOp(self))

    # def lower(self) -> StrValue:
    #     """Convert to lowercase."""
    #     from ..ops.string_ops import LowerOp

    #     return StrValue(LowerOp(self))

    # def strip(self) -> StrValue:
    #     """Strip whitespace."""
    #     from ..ops.string_ops import StripOp

    #     return StrValue(StripOp(self))

    # def split(self, separator: str = " ") -> ListValue[str]:
    #     """Split string."""
    #     from ..ops.string_ops import SplitOp
    #     from .collection_values import ListValue

    #     return ListValue(SplitOp(self, literal(separator)))

    # def replace(self, old: str, new: str) -> StrValue:
    #     """Replace substring."""
    #     from ..ops.string_ops import ReplaceOp

    #     return StrValue(ReplaceOp(self, literal(old), literal(new)))

    # def startswith(self, prefix: str | StrValue) -> BoolValue:
    #     """Check if starts with prefix."""
    #     from ..computations.string_ops import StartsWithOp

    #     return BoolValue(StartsWithOp(self, literal(prefix)))

    # def endswith(self, suffix: str | StrValue) -> BoolValue:
    #     """Check if ends with suffix."""
    #     from ..ops.string_ops import EndsWithOp

    #     return BoolValue(EndsWithOp(self, literal(suffix)))


# =============================================================================
# BYTES VALUE
# =============================================================================


class BytesValue(
    ComparisonBase["bytes | BytesValue"],
    LogicalBase["bytes | BytesValue", "BoolValue"],
    CoreBase,
    ComputedValue[bytes | SpecialValue],
):
    """RValue representing bytes.

    Supports concatenation, indexing, and slicing.

    Example:
        >>> val = BytesValue(b"hello")
        >>> combined = val + b" world"  # Returns BytesValue
        >>> first = val[0]  # Returns IntValue
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def __add__(self, other: bytes | BytesValue) -> BytesValue:
        """Concatenate bytes."""
        from ..computations.binary_ops import AddOp

        return BytesValue(AddOp(self, literal(other)))

    def __radd__(self, other: bytes) -> BytesValue:
        """Right concatenate bytes."""
        from ..computations.binary_ops import AddOp

        return BytesValue(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> IntValue: ...

    @overload
    def __getitem__(self, key: slice) -> BytesValue: ...

    def __getitem__(self, key: int | slice) -> BytesValue | IntValue:
        """Get byte or slice."""
        if isinstance(key, slice):
            from ..computations.sequence_ops import SliceOp

            return BytesValue(SliceOp[bytes](self, key.start, key.stop, key.step))

        from ..computations.sequence_ops import AtOp

        return IntValue(AtOp[int](self, literal(key)))

    def len_(self) -> IntValue:
        """Get length of bytes.

        Returns:
            Length value
        """
        from ..computations.sequence_ops import LenOp

        return IntValue(LenOp(self))


# =============================================================================
# NONE VALUE
# =============================================================================


class NoneValue(
    LogicalBase["None | NoneValue", "BoolValue"],
    CoreBase,
    ComputedValue[None | SpecialValue],
):
    """RValue representing None.

    Useful for representing absence of value in expressions.

    Example:
        >>> val = NoneValue()
        >>> is_none = val.eq(None)  # Returns BoolValue
    """

    def __init__(self, value: None | RValue = None) -> None:
        """Initialize literal with value.

        Args:
            value: The native Python value to wrap (or an RValue that computes to None)
        """
        self._value = value

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# SPECIAL VALUE TYPES
# =============================================================================


class UnknownValue(
    NumericBase["object", "UnknownValue"],
    ComparisonBase["object"],
    LogicalBase["object", "BoolValue"],
    BitwiseBase["object", "UnknownValue"],
    CoreBase,
    ComputedValue[object],
):
    """RValue representing an unknown/dynamic type.

    UnknownValue can be any type and supports all operations.
    Results remain as UnknownValue until resolved.

    Useful for:
    - Dynamic lookups where type is not known at definition time
    - Generic operations that work on any value
    - Placeholder values in expressions

    Example:
        >>> val = UnknownValue(some_dynamic_data)
        >>> result = val + 1  # Returns UnknownValue
        >>> typed = val.is_empty()  # Returns BoolValue
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return UnknownValue(operand)

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        return UnknownValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


class EmptyValue(
    CoreBase,
    ComputedValue[None],
):
    """RValue representing an empty/missing value.

    EmptyValue represents the absence of a value, distinct from None.
    It can be used as a sentinel for missing data.

    Key properties:
    - is_empty() always returns True
    - is_special() always returns True
    - or_default(x) always returns x

    Example:
        >>> empty = EmptyValue()
        >>> empty.is_empty()  # Always BoolValue(True)
        >>> empty.or_default(42)  # Returns 42
    """

    def __init__(self) -> None:
        """Initialize empty value."""
        self._value = None

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def execute(self, context: object) -> None:
        """Execute returns None for empty values.

        Args:
            context: Execution context (unused)

        Returns:
            None
        """
        return None

    def __repr__(self) -> str:
        """Return machine-friendly representation."""
        return "EmptyValue()"


class NaNValue(
    NumericBase["object", "NaNValue"],
    ComparisonBase["object"],
    CoreBase,
    ComputedValue[float],
):
    """RValue representing Not-a-Number.

    NaNValue represents an invalid numeric result (like 0/0).
    Arithmetic operations propagate NaN.

    Key properties:
    - is_nan() always returns True
    - is_special() always returns True
    - Comparisons with NaN return False (including self)
    - Arithmetic with NaN returns NaN

    Example:
        >>> nan = NaNValue()
        >>> nan.is_nan()  # Always BoolValue(True)
        >>> nan + 1  # Returns NaNValue
        >>> nan.eq(nan)  # Returns BoolValue(False)
    """

    def __init__(self) -> None:
        """Initialize NaN value."""
        self._value = float("nan")

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return NaNValue()

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_core_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def execute(self, context: object) -> float:
        """Execute returns NaN.

        Args:
            context: Execution context (unused)

        Returns:
            float('nan')
        """
        return float("nan")

    def __repr__(self) -> str:
        """Return machine-friendly representation."""
        return "NaNValue()"
