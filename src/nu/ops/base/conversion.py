"""Type conversion ops.

ToIntOp, ToFloatOp, ToBoolOp, ToStrOp, ToBytesOp, ToListOp, ToSetOp, ToTupleOp
"""

from __future__ import annotations

from nu.terms import UnaryOp


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


class ToIntOp(UnaryOp[int]):
    """Convert value to integer."""

    def apply(self, operand: object) -> int:
        """Apply."""
        return int(operand)  # type: ignore


class ToFloatOp(UnaryOp[float]):
    """Convert value to float."""

    def apply(self, operand: object) -> float:
        """Apply."""
        return float(operand)  # type: ignore


class ToBoolOp(UnaryOp[bool]):
    """Convert value to boolean."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return bool(operand)


class ToStrOp(UnaryOp[str]):
    """Convert value to string."""

    def apply(self, operand: object) -> str:
        """Apply."""
        return str(operand)


class ToBytesOp(UnaryOp[bytes]):
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

    def apply(self, operand: object) -> bytes:
        """Apply."""
        if isinstance(operand, bytes):
            return operand
        if isinstance(operand, str):
            return operand.encode(self._encoding)
        if isinstance(operand, bytearray):
            return bytes(operand)
        return bytes(operand)  # type: ignore


# =============================================================================
# COLLECTION CONVERSIONS
# =============================================================================


class ToListOp[T](UnaryOp[list[T]]):
    """Convert value to list."""

    def apply(self, operand: object) -> list[T]:
        """Apply."""
        return list(operand)  # type: ignore


class ToSetOp[T](UnaryOp[set[T]]):
    """Convert value to set."""

    def apply(self, operand: object) -> set[T]:
        """Apply."""
        return set(operand)  # type: ignore


class ToTupleOp[*Ts](UnaryOp[tuple[*Ts]]):
    """Convert value to tuple."""

    def apply(self, operand: object) -> tuple[*Ts]:
        """Apply."""
        return tuple(operand)  # type: ignore
