"""Core base class for Term types.

This module provides the CoreBase mixin that all values should inherit.
It provides fundamental operations like special value checks and conditional operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from every._abc import Type


if TYPE_CHECKING:
    from term.types import AnyType, BoolType, BytesType, FloatType, IntType, ListType, StrType
    from term.typing import Sentinel

    from every._abc import BoolArg, StrArg, Term


__all__ = [
    "BaseType",
]


class BaseType[T](Type[T]):
    """Core base that all values should inherit.

    Provides:
    - is_empty(), is_invalid(), is_sentinel() - Special value checks
    - ifelse() - Conditional/ternary operation
    - or_default() - Provide default if empty/invalid
    """

    def is_empty(self) -> BoolType:
        """Check if this value is Empty.

        Returns:
            BoolType-like result
        """
        from term.ops import IsEmptyOp
        from term.types import BoolType

        return BoolType(IsEmptyOp(self))

    def is_invalid(self) -> BoolType:
        """Check if this value is Invalid.

        Returns:
            BoolType-like result
        """
        from term.ops import IsNaNOp
        from term.types import BoolType

        return BoolType(IsNaNOp(self))

    def is_sentinel(self) -> BoolType:
        """Check if this value is a special value (Empty, Invalid, etc.).

        Returns:
            BoolType-like result
        """
        return self.is_empty().or_(self.is_invalid())

    def not_empty(self) -> BoolType:
        """Check if this value is not Empty.

        Returns:
            BoolType result
        """
        return self.is_empty().not_()

    def not_invalid(self) -> BoolType:
        """Check if this value is not Invalid.

        Returns:
            BoolType result
        """
        return self.is_invalid().not_()

    def ifelse[ElseT](
        self,
        condition: BoolArg,
        otherwise: ElseT | Term[ElseT | Sentinel],
    ) -> AnyType:
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
        from term.ops import ConditionalOp
        from term.types import AnyType

        # ConditionalOp expects: (value_if_true, condition, value_if_false)
        return AnyType(ConditionalOp(self, condition, otherwise))

    def or_default[DefaultT](self, default: DefaultT | Term[DefaultT]) -> AnyType:
        """Return self if not empty/invalid, otherwise return default.

        Args:
            default: Default value if self is empty or invalid

        Returns:
            Self if valid, default otherwise

        Example:
            >>> value.or_default(0)  # Returns 0 if value is Empty
        """
        from term.types import AnyType

        # ifelse returns self if condition is true, otherwise returns the alternative
        # We want: return self if NOT sentinel, return default if sentinel
        return AnyType(self.ifelse(self.is_sentinel().not_(), default))

    # =========================================================================
    # TYPE CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntType:
        """Convert this value to an integer.

        Returns:
            IntType containing the converted integer

        Example:
            >>> float_val.to_int()  # 3.14 -> 3
            >>> str_val.to_int()  # "42" -> 42
        """
        from term.ops import ToIntOp
        from term.types import IntType

        return IntType(ToIntOp(self))

    def to_float(self) -> FloatType:
        """Convert this value to a float.

        Returns:
            FloatType containing the converted float

        Example:
            >>> int_val.to_float()  # 42 -> 42.0
            >>> str_val.to_float()  # "3.14" -> 3.14
        """
        from term.ops import ToFloatOp
        from term.types import FloatType

        return FloatType(ToFloatOp(self))

    def to_bool(self) -> BoolType:
        """Convert this value to a boolean.

        Returns:
            BoolType containing the converted boolean

        Example:
            >>> int_val.to_bool()  # 0 -> False, 1 -> True
            >>> str_val.to_bool()  # "" -> False, "x" -> True
        """
        from term.ops import ToBoolOp
        from term.types import BoolType

        return BoolType(ToBoolOp(self))

    def to_str(self) -> StrType:
        """Convert this value to a string.

        Returns:
            StrType containing the converted string

        Example:
            >>> int_val.to_str()  # 42 -> "42"
            >>> datetime_val.to_str()  # datetime -> "2024-01-15 10:30:00"
        """
        from term.ops import ToStrOp
        from term.types import StrType

        return StrType(ToStrOp(self))

    def to_bytes(self, encoding: StrArg = "utf-8") -> BytesType:
        """Convert this value to bytes.

        Args:
            encoding: Encoding to use for string conversion

        Returns:
            BytesType containing the converted bytes

        Example:
            >>> str_val.to_bytes()  # "hello" -> b"hello"
        """
        from term.ops import ToBytesOp
        from term.types import BytesType

        return BytesType(ToBytesOp(self, encoding))

    def to_list(self) -> ListType:
        """Convert this value to a list.

        Returns:
            ListType containing the converted list

        Example:
            >>> tuple_val.to_list()  # (1, 2, 3) -> [1, 2, 3]
            >>> set_val.to_list()  # {1, 2, 3} -> [1, 2, 3]
        """
        from term.ops import ToListOp
        from term.types import ListType

        return ListType(ToListOp(self))
