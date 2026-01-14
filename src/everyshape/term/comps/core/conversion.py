"""Type conversion operations.

This module provides operations for converting values between types:

ToIntOp, ToFloatOp, ToBoolOp, ToStrOp, ToBytesOp, ToListOp, ToSetOp, ToTupleOp

These enable chaining conversions in the DSL, e.g.:
    datetime_value.to_str()  # Convert datetime to string
    some_value.to_int()      # Convert to integer

Design principles:
1. Atomic classes: one conversion = one class
2. All inherit from ConversionOp base
3. Graceful degradation: return NaN on conversion failure
4. Type safety: each op specifies its result type
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.typing import NAN, Sentinel

from ...term import Operation


if TYPE_CHECKING:
    from ...context import Context
    from ...term import Term
    from ...type import UnionBaseType


__all__ = [
    "ConversionOp",
    "ToBoolOp",
    "ToBytesOp",
    "ToFloatOp",
    "ToIntOp",
    "ToListOp",
    "ToSetOp",
    "ToStrOp",
    "ToTupleOp",
]


type OpArgument = Term | UnionBaseType


# =============================================================================
# BASE CONVERSION OPERATION
# =============================================================================


class ConversionOp[ResultT](Operation[ResultT | Sentinel]):
    """Base class for type conversion operations.

    Defines execution pattern: evaluate operand → apply conversion → return result.
    Returns NaN if conversion fails.

    Subclasses implement specific conversions (ToIntOp, ToStrOp, etc.).
    """

    def __init__(self, operand: OpArgument) -> None:
        """Initialize conversion operation.

        Args:
            operand: Value to convert
        """
        self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> ResultT | Sentinel:
        """Execute conversion operation.

        Args:
            context: Execution context

        Returns:
            Converted value, or NaN if conversion fails
        """
        operand_val = self.children[0].execute(context)
        return self._convert(value=operand_val)

    def _convert(self, value: object) -> ResultT | Sentinel:
        """Apply the conversion to value.

        Subclasses override with conversion-specific logic.

        Args:
            value: Value to convert

        Returns:
            Converted value or NaN for errors
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r})"


# =============================================================================
# PRIMITIVE CONVERSIONS
# =============================================================================


class ToIntOp(ConversionOp[int]):
    """Convert value to integer."""

    def _convert(self, value: object) -> int | Sentinel:
        try:
            return int(value)  # type: ignore
        except (TypeError, ValueError):
            return NAN


class ToFloatOp(ConversionOp[float]):
    """Convert value to float."""

    def _convert(self, value: object) -> float | Sentinel:
        try:
            return float(value)  # type: ignore
        except (TypeError, ValueError):
            return NAN


class ToBoolOp(ConversionOp[bool]):
    """Convert value to boolean."""

    def _convert(self, value: object) -> bool | Sentinel:
        try:
            return bool(value)
        except (TypeError, ValueError):
            return NAN


class ToStrOp(ConversionOp[str]):
    """Convert value to string."""

    def _convert(self, value: object) -> str | Sentinel:
        try:
            return str(value)
        except (TypeError, ValueError):
            return NAN


class ToBytesOp(ConversionOp[bytes]):
    """Convert value to bytes.

    Supports:
    - str -> bytes (using UTF-8 encoding)
    - bytes -> bytes (passthrough)
    - bytearray -> bytes
    - Iterables of ints -> bytes
    """

    def __init__(self, operand: OpArgument, encoding: str = "utf-8") -> None:
        """Initialize bytes conversion.

        Args:
            operand: Value to convert
            encoding: Encoding to use for string conversion
        """
        super().__init__(operand)
        self._encoding = encoding

    def _convert(self, value: object) -> bytes | Sentinel:
        try:
            if isinstance(value, bytes):
                return value
            if isinstance(value, str):
                return value.encode(self._encoding)
            if isinstance(value, bytearray):
                return bytes(value)
            return bytes(value)  # type: ignore
        except (TypeError, ValueError, UnicodeEncodeError):
            return NAN


# =============================================================================
# COLLECTION CONVERSIONS
# =============================================================================


class ToListOp[T](ConversionOp[list[T]]):
    """Convert value to list."""

    def _convert(self, value: object) -> list[T] | Sentinel:
        try:
            return list(value)  # type: ignore
        except TypeError:
            return NAN


class ToSetOp[T](ConversionOp[set[T]]):
    """Convert value to set."""

    def _convert(self, value: object) -> set[T] | Sentinel:
        try:
            return set(value)  # type: ignore
        except TypeError:
            return NAN


class ToTupleOp[*Ts](ConversionOp[tuple[*Ts]]):
    """Convert value to tuple."""

    def _convert(self, value: object) -> tuple[*Ts] | Sentinel:
        try:
            return tuple(value)  # type: ignore
        except TypeError:
            return NAN
