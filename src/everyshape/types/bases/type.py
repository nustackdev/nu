"""Core base class for Term types.

This module provides the CoreBase mixin that all values should inherit.
It provides fundamental operations like special value checks and conditional operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.term import Type as BaseType
from everyshape.term import literal


if TYPE_CHECKING:
    from everyshape.term import BoolArg, Term
    from everyshape.types import AnyType, BoolType, BytesType, FloatType, IntType, ListType, StrType
    from everyshape.typing import Sentinel


__all__ = [
    "Type",
]


class Type[T](BaseType[T]):
    """Core base that all values should inherit.

    Provides:
    - is_empty(), is_nan(), is_sentinel() - Special value checks
    - ifelse() - Conditional/ternary operation
    - or_default() - Provide default if empty/nan
    """

    def is_empty(self) -> BoolType:
        """Check if this value is Empty.

        Returns:
            BoolType-like result
        """
        from everyshape.ops import IsEmptyOp
        from everyshape.types import BoolType

        return BoolType(IsEmptyOp(self))

    def is_nan(self) -> BoolType:
        """Check if this value is NaN.

        Returns:
            BoolType-like result
        """
        from everyshape.ops import IsNaNOp
        from everyshape.types import BoolType

        return BoolType(IsNaNOp(self))

    def is_sentinel(self) -> BoolType:
        """Check if this value is a special value (Empty, NaN, etc.).

        Returns:
            BoolType-like result
        """
        return self.is_empty().or_(self.is_nan())

    def not_empty(self) -> BoolType:
        """Check if this value is not Empty.

        Returns:
            BoolType result
        """
        return self.is_empty().not_()

    def not_nan(self) -> BoolType:
        """Check if this value is not NaN.

        Returns:
            BoolType result
        """
        return self.is_nan().not_()

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
        from everyshape.ops import ConditionalOp
        from everyshape.types import AnyType

        return AnyType(ConditionalOp(literal(condition), self, literal(otherwise)))

    def or_default[DefaultT](self, default: DefaultT | Term[DefaultT]) -> AnyType:
        """Return self if not empty/nan, otherwise return default.

        Args:
            default: Default value if self is empty or nan

        Returns:
            Self if valid, default otherwise

        Example:
            >>> value.or_default(0)  # Returns 0 if value is Empty
        """
        from everyshape.types import AnyType

        return AnyType(self.ifelse(self.is_sentinel(), literal(default)))

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
        from everyshape.ops import ToIntOp
        from everyshape.types import IntType

        return IntType(ToIntOp(self))

    def to_float(self) -> FloatType:
        """Convert this value to a float.

        Returns:
            FloatType containing the converted float

        Example:
            >>> int_val.to_float()  # 42 -> 42.0
            >>> str_val.to_float()  # "3.14" -> 3.14
        """
        from everyshape.ops import ToFloatOp
        from everyshape.types import FloatType

        return FloatType(ToFloatOp(self))

    def to_bool(self) -> BoolType:
        """Convert this value to a boolean.

        Returns:
            BoolType containing the converted boolean

        Example:
            >>> int_val.to_bool()  # 0 -> False, 1 -> True
            >>> str_val.to_bool()  # "" -> False, "x" -> True
        """
        from everyshape.ops import ToBoolOp
        from everyshape.types import BoolType

        return BoolType(ToBoolOp(self))

    def to_str(self) -> StrType:
        """Convert this value to a string.

        Returns:
            StrType containing the converted string

        Example:
            >>> int_val.to_str()  # 42 -> "42"
            >>> datetime_val.to_str()  # datetime -> "2024-01-15 10:30:00"
        """
        from everyshape.ops import ToStrOp
        from everyshape.types import StrType

        return StrType(ToStrOp(self))

    def to_bytes(self, encoding: str = "utf-8") -> BytesType:
        """Convert this value to bytes.

        Args:
            encoding: Encoding to use for string conversion

        Returns:
            BytesType containing the converted bytes

        Example:
            >>> str_val.to_bytes()  # "hello" -> b"hello"
        """
        from everyshape.ops import ToBytesOp
        from everyshape.types import BytesType

        return BytesType(ToBytesOp(self, encoding))

    def to_list(self) -> ListType:
        """Convert this value to a list.

        Returns:
            ListType containing the converted list

        Example:
            >>> tuple_val.to_list()  # (1, 2, 3) -> [1, 2, 3]
            >>> set_val.to_list()  # {1, 2, 3} -> [1, 2, 3]
        """
        from everyshape.ops import ToListOp
        from everyshape.types import ListType

        return ListType(ToListOp(self))
