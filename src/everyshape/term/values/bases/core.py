"""Core base class for RValue types.

This module provides the CoreBase mixin that all values should inherit.
It provides fundamental operations like special value checks and conditional operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..conversion import literal


if TYPE_CHECKING:
    from everyshape.types import SpecialValue

    from ...term import RValue
    from ..values import (
        BoolValue,
        BytesValue,
        FloatValue,
        IntValue,
        ListValue,
        StrValue,
        UnknownValue,
    )


__all__ = [
    "CoreBase",
]


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
        from ...comps.value.unary_ops import IsEmptyOp
        from ..values import BoolValue

        return BoolValue(IsEmptyOp(self))

    def is_nan(self) -> BoolValue:
        """Check if this value is NaN.

        Returns:
            BoolValue-like result
        """
        from ...comps.value.unary_ops import IsNaNOp
        from ..values import BoolValue

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
        from ...comps.value.ternary_ops import ConditionalOp
        from ..values import UnknownValue

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
        from ..values import UnknownValue

        return UnknownValue(self.ifelse(self.is_special(), literal(default)))

    # =========================================================================
    # TYPE CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntValue:
        """Convert this value to an integer.

        Returns:
            IntValue containing the converted integer

        Example:
            >>> float_val.to_int()  # 3.14 -> 3
            >>> str_val.to_int()  # "42" -> 42
        """
        from ...comps.value.conversion import ToIntOp
        from ..values import IntValue

        return IntValue(ToIntOp(self))

    def to_float(self) -> FloatValue:
        """Convert this value to a float.

        Returns:
            FloatValue containing the converted float

        Example:
            >>> int_val.to_float()  # 42 -> 42.0
            >>> str_val.to_float()  # "3.14" -> 3.14
        """
        from ...comps.value.conversion import ToFloatOp
        from ..values import FloatValue

        return FloatValue(ToFloatOp(self))

    def to_bool(self) -> BoolValue:
        """Convert this value to a boolean.

        Returns:
            BoolValue containing the converted boolean

        Example:
            >>> int_val.to_bool()  # 0 -> False, 1 -> True
            >>> str_val.to_bool()  # "" -> False, "x" -> True
        """
        from ...comps.value.conversion import ToBoolOp
        from ..values import BoolValue

        return BoolValue(ToBoolOp(self))

    def to_str(self) -> StrValue:
        """Convert this value to a string.

        Returns:
            StrValue containing the converted string

        Example:
            >>> int_val.to_str()  # 42 -> "42"
            >>> datetime_val.to_str()  # datetime -> "2024-01-15 10:30:00"
        """
        from ...comps.value.conversion import ToStrOp
        from ..values import StrValue

        return StrValue(ToStrOp(self))

    def to_bytes(self, encoding: str = "utf-8") -> BytesValue:
        """Convert this value to bytes.

        Args:
            encoding: Encoding to use for string conversion

        Returns:
            BytesValue containing the converted bytes

        Example:
            >>> str_val.to_bytes()  # "hello" -> b"hello"
        """
        from ...comps.value.conversion import ToBytesOp
        from ..values import BytesValue

        return BytesValue(ToBytesOp(self, encoding))

    def to_list[T](self) -> ListValue[T]:
        """Convert this value to a list.

        Returns:
            ListValue containing the converted list

        Example:
            >>> tuple_val.to_list()  # (1, 2, 3) -> [1, 2, 3]
            >>> set_val.to_list()  # {1, 2, 3} -> [1, 2, 3]
        """
        from ...comps.value.conversion import ToListOp
        from ..values import ListValue

        return ListValue(ToListOp(self))
