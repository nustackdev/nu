"""Type conversion morphisms.

ToIntOp, ToFloatOp, ToBoolOp, ToStrOp, ToBytesOp, ToListOp, ToSetOp, ToTupleOp

All conversions return Invalid on conversion failure.
"""

from __future__ import annotations

from every import INVALID, Operation, Sentinel, UnaryMorphism


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


class ToIntOp(Operation, UnaryMorphism[int | Sentinel]):
    """Convert value to integer."""

    def _apply(self, operand: object) -> int | Sentinel:
        try:
            return int(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class ToFloatOp(Operation, UnaryMorphism[float | Sentinel]):
    """Convert value to float."""

    def _apply(self, operand: object) -> float | Sentinel:
        try:
            return float(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class ToBoolOp(Operation, UnaryMorphism[bool | Sentinel]):
    """Convert value to boolean."""

    def _apply(self, operand: object) -> bool | Sentinel:
        try:
            return bool(operand)
        except (TypeError, ValueError):
            return INVALID


class ToStrOp(Operation, UnaryMorphism[str | Sentinel]):
    """Convert value to string."""

    def _apply(self, operand: object) -> str | Sentinel:
        try:
            return str(operand)
        except (TypeError, ValueError):
            return INVALID


class ToBytesOp(Operation, UnaryMorphism[bytes | Sentinel]):
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

    def _apply(self, operand: object) -> bytes | Sentinel:
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


class ToListOp[T](Operation, UnaryMorphism[list[T] | Sentinel]):
    """Convert value to list."""

    def _apply(self, operand: object) -> list[T] | Sentinel:
        try:
            return list(operand)  # type: ignore
        except TypeError:
            return INVALID


class ToSetOp[T](Operation, UnaryMorphism[set[T] | Sentinel]):
    """Convert value to set."""

    def _apply(self, operand: object) -> set[T] | Sentinel:
        try:
            return set(operand)  # type: ignore
        except TypeError:
            return INVALID


class ToTupleOp[*Ts](Operation, UnaryMorphism[tuple[*Ts] | Sentinel]):
    """Convert value to tuple."""

    def _apply(self, operand: object) -> tuple[*Ts] | Sentinel:
        try:
            return tuple(operand)  # type: ignore
        except TypeError:
            return INVALID
