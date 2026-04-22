"""Type conversion ops.

ToInt, ToFloat, ToBool, ToStr, ToBytes, ToList, ToSet, ToTuple
"""

from __future__ import annotations

from nu.terms import UnaryScalar


__all__ = [
    "ToBool",
    "ToBytes",
    "ToFloat",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
    "ToTuple",
]


# =============================================================================
# PRIMITIVE CONVERSIONS
# =============================================================================


class ToInt(UnaryScalar[int]):
    """Convert value to integer."""

    def apply(self, operand: object) -> int:
        """Apply."""
        return int(operand)  # type: ignore


class ToFloat(UnaryScalar[float]):
    """Convert value to float."""

    def apply(self, operand: object) -> float:
        """Apply."""
        return float(operand)  # type: ignore


class ToBool(UnaryScalar[bool]):
    """Convert value to boolean."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return bool(operand)


class ToStr(UnaryScalar[str]):
    """Convert value to string."""

    def apply(self, operand: object) -> str:
        """Apply."""
        return str(operand)


class ToBytes(UnaryScalar[bytes]):
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


class ToList[T](UnaryScalar[list[T]]):
    """Convert value to list."""

    def apply(self, operand: object) -> list[T]:
        """Apply."""
        return list(operand)  # type: ignore


class ToSet[T](UnaryScalar[set[T]]):
    """Convert value to set."""

    def apply(self, operand: object) -> set[T]:
        """Apply."""
        return set(operand)  # type: ignore


class ToTuple[*Ts](UnaryScalar[tuple[*Ts]]):
    """Convert value to tuple."""

    def apply(self, operand: object) -> tuple[*Ts]:
        """Apply."""
        return tuple(operand)  # type: ignore
