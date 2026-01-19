"""Type conversion operations.

ToIntOp, ToFloatOp, ToBoolOp, ToStrOp, ToBytesOp, ToListOp, ToSetOp, ToTupleOp

All conversions inherit from UnaryOp and return Invalid on conversion failure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyterm.term import UnaryOp
from everyterm.typing import INVALID, Sentinel


if TYPE_CHECKING:
    from ..term import Term


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


class ToIntOp(UnaryOp[int | Sentinel]):
    """Convert value to integer."""

    def _apply_op(self, operand: object) -> int | Sentinel:
        try:
            return int(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class ToFloatOp(UnaryOp[float | Sentinel]):
    """Convert value to float."""

    def _apply_op(self, operand: object) -> float | Sentinel:
        try:
            return float(operand)  # type: ignore
        except (TypeError, ValueError):
            return INVALID


class ToBoolOp(UnaryOp[bool | Sentinel]):
    """Convert value to boolean."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        try:
            return bool(operand)
        except (TypeError, ValueError):
            return INVALID


class ToStrOp(UnaryOp[str | Sentinel]):
    """Convert value to string."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        try:
            return str(operand)
        except (TypeError, ValueError):
            return INVALID


class ToBytesOp(UnaryOp[bytes | Sentinel]):
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
        self.children = (cast("Term", operand),)
        self._encoding = encoding

    def _apply_op(self, operand: object) -> bytes | Sentinel:
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


class ToListOp[T](UnaryOp[list[T] | Sentinel]):
    """Convert value to list."""

    def _apply_op(self, operand: object) -> list[T] | Sentinel:
        try:
            return list(operand)  # type: ignore
        except TypeError:
            return INVALID


class ToSetOp[T](UnaryOp[set[T] | Sentinel]):
    """Convert value to set."""

    def _apply_op(self, operand: object) -> set[T] | Sentinel:
        try:
            return set(operand)  # type: ignore
        except TypeError:
            return INVALID


class ToTupleOp[*Ts](UnaryOp[tuple[*Ts] | Sentinel]):
    """Convert value to tuple."""

    def _apply_op(self, operand: object) -> tuple[*Ts] | Sentinel:
        try:
            return tuple(operand)  # type: ignore
        except TypeError:
            return INVALID
