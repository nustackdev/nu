"""Type conversion morphisms.

ToIntOp, ToFloatOp, ToBoolOp, ToStrOp, ToBytesOp, ToListOp, ToSetOp, ToTupleOp

All conversions return Invalid on conversion failure.
"""

from __future__ import annotations

from everybase.core import INVALID, Sentinel, UnaryOperation


__all__ = [
    "ToBoolOp",
    "ToBytesOp",
    "ToFloatOp",
    "ToIntOp",
    "ToListOp",
    "ToSetOp",
    "ToStrOp",
    "ToTupleOp",
]


# =============================================================================
# PRIMITIVE CONVERSIONS
# =============================================================================


class ToIntOp(UnaryOperation[int]):
    """Convert value to integer."""

    def apply(self, operand: object) -> int | Sentinel:
        """Apply."""
        try:
            return int(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class ToFloatOp(UnaryOperation[float]):
    """Convert value to float."""

    def apply(self, operand: object) -> float | Sentinel:
        """Apply."""
        try:
            return float(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class ToBoolOp(UnaryOperation[bool]):
    """Convert value to boolean."""

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        try:
            return bool(operand)
        except (TypeError, ValueError):
            return INVALID


class ToStrOp(UnaryOperation[str]):
    """Convert value to string."""

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        try:
            return str(operand)
        except (TypeError, ValueError):
            return INVALID


class ToBytesOp(UnaryOperation[bytes]):
    """Convert value to bytes.

    Supports:
    - str -> bytes (using UTF-8 encoding by default)
    - bytes -> bytes (passthrough)
    - bytearray -> bytes
    - Iterables of ints -> bytes
    """

    def __init__(self, operand: object, encoding: str = "utf-8") -> None:
        """Initialize bytes conversion.

        Args:
            operand: Value to convert
            encoding: Encoding to use for string conversion
        """
        super().__init__(operand)
        self._encoding = encoding

    def apply(self, operand: object) -> bytes | Sentinel:
        """Apply."""
        try:
            if isinstance(operand, bytes):
                return operand
            if isinstance(operand, str):
                return operand.encode(self._encoding)
            if isinstance(operand, bytearray):
                return bytes(operand)
            return bytes(operand)  # type: ignore
        except (TypeError, ValueError, UnicodeEncodeError):
            return INVALID


# =============================================================================
# COLLECTION CONVERSIONS
# =============================================================================


class ToListOp[T](UnaryOperation[list[T]]):
    """Convert value to list."""

    def apply(self, operand: object) -> list[T] | Sentinel:
        """Apply."""
        try:
            return list(operand)  # type: ignore
        except TypeError:
            return INVALID


class ToSetOp[T](UnaryOperation[set[T]]):
    """Convert value to set."""

    def apply(self, operand: object) -> set[T] | Sentinel:
        """Apply."""
        try:
            return set(operand)  # type: ignore
        except TypeError:
            return INVALID


class ToTupleOp[*Ts](UnaryOperation[tuple[*Ts]]):
    """Convert value to tuple."""

    def apply(self, operand: object) -> tuple[*Ts] | Sentinel:
        """Apply."""
        try:
            return tuple(operand)  # type: ignore
        except TypeError:
            return INVALID
