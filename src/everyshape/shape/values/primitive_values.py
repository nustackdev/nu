"""Primitive RValue implementations.

This module provides concrete RValue types for Python primitives:
- IntValue: Integer values
- FloatValue: Floating-point values
- BoolValue: Boolean values
- StrValue: String values
- BytesValue: Bytes values
- NoneValue: None value

These wrap native Python values and enable DSL operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from .base import Literal
from .bases import (
    ArithmeticBase,
    BitwiseBase,
    ComparisonBase,
    LogicalBase,
)
from .conversion import literal


if TYPE_CHECKING:
    from ..term import RValue


__all__ = [
    "BoolValue",
    "BytesValue",
    "FloatValue",
    "IntValue",
    "NoneValue",
    "StrValue",
]


# =============================================================================
# INTEGER VALUE
# =============================================================================


class IntValue(
    ArithmeticBase[
        "int | float | FloatValue | IntValue",
        "FloatValue | IntValue",
    ],
    ComparisonBase["int | float | FloatValue | IntValue", "BoolValue"],
    LogicalBase["int | float | FloatValue | IntValue", "BoolValue"],
    BitwiseBase[
        "int | float | FloatValue | IntValue",
        "FloatValue | IntValue",
    ],
    Literal[int],
):
    """RValue representing an integer.

    Supports full arithmetic, comparison, and bitwise operations.
    Operations return appropriate RValue types.
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return FloatValue(operand)

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        return FloatValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# FLOAT VALUE
# =============================================================================


class FloatValue(
    ArithmeticBase[
        "int | float | FloatValue | IntValue",
        "FloatValue | IntValue",
    ],
    ComparisonBase["int | float | FloatValue | IntValue", "BoolValue"],
    LogicalBase["int | float | FloatValue | IntValue", "BoolValue"],
    BitwiseBase[
        "int | float | FloatValue | IntValue",
        "FloatValue | IntValue",
    ],
    Literal[float],
):
    """RValue representing a floating-point number.

    Supports full arithmetic and comparison operations.
    Does not support bitwise operations.

    Example:
        >>> val = FloatValue(3.14)
        >>> doubled = val * 2  # Returns MulOp
        >>> is_positive = val > 0  # Returns GtOp
    """

    def _wrap_arithmetic_result(self, operand: RValue) -> RValue:
        return FloatValue(operand)

    def _wrap_bitwise_result(self, operand: RValue) -> RValue:
        return FloatValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# BOOL VALUE
# =============================================================================


class BoolValue(
    LogicalBase["bool | BoolValue", "BoolValue"],
    ComparisonBase["bool | BoolValue", "BoolValue"],
    Literal[bool],
):
    """RValue representing a boolean.

    Supports logical operations: and_, or_, not_.

    Example:
        >>> val = BoolValue(True)
        >>> combined = val.and_(other)  # Returns AndOp
        >>> negated = val.not_()  # Returns NotOp
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)


# =============================================================================
# STRING VALUE
# =============================================================================


class StrValue(
    ComparisonBase["str | StrValue", "BoolValue"],
    LogicalBase["str | StrValue", "BoolValue"],
    Literal[str],
):
    """RValue representing a string.

    Supports concatenation, indexing, slicing, and string operations.

    Example:
        >>> val = StrValue("hello")
        >>> greeting = val + " world"  # Returns AddOp
        >>> first = val[0]  # Returns AtOp
        >>> length = val.len_()  # Returns LenOp
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def __add__(self, other: str) -> StrValue:
        """Concatenate strings."""
        from ..ops.binary_ops import AddOp

        return StrValue(AddOp(self, literal(other)))

    def __radd__(self, other: str) -> StrValue:
        """Right concatenate strings."""
        from ..ops.binary_ops import AddOp

        return StrValue(AddOp(literal(other), self))

    def __getitem__(self, key: int | slice) -> StrValue:
        """Get character or substring."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return StrValue(SliceOp(self, key.start, key.stop, key.step))

        from ..ops.sequence_ops import AtOp

        return StrValue(AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get string length.

        Returns:
            Length value
        """
        from ..ops.sequence_ops import LenOp

        return IntValue(LenOp(self))

    def contains(self, substring: str) -> BoolValue:
        """Check if contains substring.

        Args:
            substring: Substring to find

        Returns:
            Boolean result
        """
        from ..ops.mapping_ops import ContainsOp

        return BoolValue(ContainsOp(self, literal(substring)))


# =============================================================================
# BYTES VALUE
# =============================================================================


class BytesValue(
    ComparisonBase["bytes | BytesValue", "BoolValue"],
    LogicalBase["bytes | BytesValue", "BoolValue"],
    Literal[bytes],
):
    """RValue representing bytes.

    Supports concatenation, indexing, and slicing.

    Example:
        >>> val = BytesValue(b"hello")
        >>> combined = val + b" world"  # Returns AddOp
        >>> first = val[0]  # Returns AtOp
    """

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)

    def __add__(self, other: bytes | BytesValue) -> BytesValue:
        """Concatenate bytes."""
        from ..ops.binary_ops import AddOp

        return BytesValue(AddOp(self, literal(other)))

    def __radd__(self, other: bytes) -> BytesValue:
        """Right concatenate bytes."""
        from ..ops.binary_ops import AddOp

        return BytesValue(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> IntValue: ...

    @overload
    def __getitem__(self, key: slice) -> BytesValue: ...

    def __getitem__(self, key: int | slice) -> BytesValue | IntValue:
        """Get byte or slice."""
        if isinstance(key, slice):
            from ..ops.sequence_ops import SliceOp

            return BytesValue(SliceOp(self, key.start, key.stop, key.step))

        from ..ops.sequence_ops import AtOp

        return IntValue(AtOp(self, literal(key)))

    def len_(self) -> IntValue:
        """Get length of bytes.

        Returns:
            Length value
        """
        from ..ops.sequence_ops import LenOp

        return IntValue(LenOp(self))


# =============================================================================
# NONE VALUE
# =============================================================================


class NoneValue(
    LogicalBase["None | NoneValue", "BoolValue"],
    Literal[None],
):
    """RValue representing None.

    Useful for representing absence of value in expressions.

    Example:
        >>> val = NoneValue()
        >>> is_none = val.eq(None)  # Returns EqOp
    """

    def __init__(self, value: None | RValue = None) -> None:
        """Initialize literal with value.

        Args:
            value: The native Python value to wrap (or an RValue that computes to None)
        """
        self._value = value

    def _wrap_logical_result(self, operand: RValue) -> RValue:
        return BoolValue(operand)
