"""Bytes-specific ops.

Decoding: DecodeOp, HexOp
Case transformation: BytesUpperOp, BytesLowerOp
Stripping: BytesStripOp, BytesLStripOp, BytesRStripOp
Splitting: BytesSplitOp
Searching: BytesFindOp, BytesCountOp
Testing: BytesStartsWithOp, BytesEndsWithOp
Replacing: BytesReplaceOp

All ops use every.Op base classes with Calculation mixin (pure).
"""

from __future__ import annotations

from nu.terms import (
    INVALID,
    BinaryCalc,
    NAryCalc,
    Sentinel,
    TernaryCalc,
    UnaryCalc,
)


__all__ = [
    "BytesCountOp",
    "BytesEndsWithOp",
    "BytesFindOp",
    "BytesLStripOp",
    "BytesLowerOp",
    "BytesRStripOp",
    "BytesReplaceOp",
    "BytesSplitOp",
    "BytesStartsWithOp",
    "BytesStripOp",
    "BytesUpperOp",
    "DecodeOp",
    "HexOp",
]


# =============================================================================
# DECODING
# =============================================================================


class DecodeOp(BinaryCalc[str]):
    """Decode bytes to string: bytes.decode(encoding)."""

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, bytes):
            return INVALID
        try:
            return left.decode(str(right))
        except (UnicodeDecodeError, LookupError):
            return INVALID


class HexOp(UnaryCalc[str]):
    """Convert to hex string: bytes.hex()."""

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, bytes):
            return INVALID
        return operand.hex()


# =============================================================================
# CASE TRANSFORMATION
# =============================================================================


class BytesUpperOp(UnaryCalc[bytes]):
    """Convert to uppercase: bytes.upper()."""

    def apply(self, operand: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(operand, bytes):
            return INVALID
        return operand.upper()


class BytesLowerOp(UnaryCalc[bytes]):
    """Convert to lowercase: bytes.lower()."""

    def apply(self, operand: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(operand, bytes):
            return INVALID
        return operand.lower()


# =============================================================================
# STRIPPING
# =============================================================================


class BytesStripOp(BinaryCalc[bytes]):
    """Strip bytes: bytes.strip(chars)."""

    def apply(self, left: object, right: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(left, bytes):
            return INVALID
        if right is not None and not isinstance(right, bytes):
            return INVALID
        return left.strip(right)


class BytesLStripOp(BinaryCalc[bytes]):
    """Strip leading bytes: bytes.lstrip(chars)."""

    def apply(self, left: object, right: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(left, bytes):
            return INVALID
        if right is not None and not isinstance(right, bytes):
            return INVALID
        return left.lstrip(right)


class BytesRStripOp(BinaryCalc[bytes]):
    """Strip trailing bytes: bytes.rstrip(chars)."""

    def apply(self, left: object, right: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(left, bytes):
            return INVALID
        if right is not None and not isinstance(right, bytes):
            return INVALID
        return left.rstrip(right)


# =============================================================================
# SPLITTING
# =============================================================================


class BytesSplitOp(TernaryCalc[list[bytes]]):
    """Split bytes: bytes.split(sep, maxsplit)."""

    def apply(self, first: object, second: object, third: object) -> list[bytes] | Sentinel:
        """Apply."""
        if not isinstance(first, bytes):
            return INVALID
        if second is not None and not isinstance(second, bytes):
            return INVALID
        return first.split(second, int(third))  # type: ignore[arg-type]


# =============================================================================
# SEARCHING
# =============================================================================


class BytesFindOp(NAryCalc[int]):
    """Find sub-bytes: bytes.find(sub, start, end)."""

    def apply(self, *args: object) -> int | Sentinel:
        """Apply."""
        operand, sub, start, end = args
        if not isinstance(operand, bytes) or not isinstance(sub, bytes):
            return INVALID
        if end is None:
            return operand.find(sub, int(start))  # type: ignore[arg-type]
        return operand.find(sub, int(start), int(end))  # type: ignore[arg-type]


class BytesCountOp(BinaryCalc[int]):
    """Count sub-bytes occurrences: bytes.count(sub)."""

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.count(right)


# =============================================================================
# PREFIX/SUFFIX TESTING
# =============================================================================


class BytesStartsWithOp(BinaryCalc[bool]):
    """Check if starts with prefix: bytes.startswith(prefix)."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.startswith(right)


class BytesEndsWithOp(BinaryCalc[bool]):
    """Check if ends with suffix: bytes.endswith(suffix)."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.endswith(right)


# =============================================================================
# REPLACING
# =============================================================================


class BytesReplaceOp(NAryCalc[bytes]):
    """Replace sub-bytes: bytes.replace(old, new, count)."""

    def apply(self, *args: object) -> bytes | Sentinel:
        """Apply."""
        operand, old, new, count = args
        if (
            not isinstance(operand, bytes)
            or not isinstance(old, bytes)
            or not isinstance(new, bytes)
        ):
            return INVALID
        count_int = int(count)  # type: ignore[arg-type]
        if count_int == -1:
            return operand.replace(old, new)
        return operand.replace(old, new, count_int)
