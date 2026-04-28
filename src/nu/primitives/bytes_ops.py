"""Bytes-specific ops.

Decoding: DecodeOp, HexOp
Case transformation: BytesUpperOp, BytesLowerOp
Stripping: BytesStripOp, BytesLStripOp, BytesRStripOp
Splitting: BytesSplitOp
Searching: BytesFindOp, BytesCountOp
Testing: BytesStartsWithOp, BytesEndsWithOp
Replacing: BytesReplaceOp
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import (
    INVALID,
    BinaryQuery,
    Mode,
    ScalarQuery,
    Sentinel,
    TernaryQuery,
    UnaryQuery,
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


class DecodeOp(BinaryQuery[str]):
    """Decode bytes to string: bytes.decode(encoding)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, bytes):
            return INVALID
        try:
            return left.decode(str(right))
        except (UnicodeDecodeError, LookupError):
            return INVALID


class HexOp(UnaryQuery[str]):
    """Convert to hex string: bytes.hex()."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, bytes):
            return INVALID
        return operand.hex()


# =============================================================================
# CASE TRANSFORMATION
# =============================================================================


class BytesUpperOp(UnaryQuery[bytes]):
    """Convert to uppercase: bytes.upper()."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(operand, bytes):
            return INVALID
        return operand.upper()


class BytesLowerOp(UnaryQuery[bytes]):
    """Convert to lowercase: bytes.lower()."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(operand, bytes):
            return INVALID
        return operand.lower()


# =============================================================================
# STRIPPING
# =============================================================================


class BytesStripOp(BinaryQuery[bytes]):
    """Strip bytes: bytes.strip(chars)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(left, bytes):
            return INVALID
        if right is not None and not isinstance(right, bytes):
            return INVALID
        return left.strip(right)


class BytesLStripOp(BinaryQuery[bytes]):
    """Strip leading bytes: bytes.lstrip(chars)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(left, bytes):
            return INVALID
        if right is not None and not isinstance(right, bytes):
            return INVALID
        return left.lstrip(right)


class BytesRStripOp(BinaryQuery[bytes]):
    """Strip trailing bytes: bytes.rstrip(chars)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

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


class BytesSplitOp(TernaryQuery[list[bytes]]):
    """Split bytes: bytes.split(sep, maxsplit)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

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


class BytesFindOp(ScalarQuery[int]):
    """Find sub-bytes: bytes.find(sub, start, end)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, *args: object) -> int | Sentinel:
        """Apply."""
        operand, sub, start, end = args
        if not isinstance(operand, bytes) or not isinstance(sub, bytes):
            return INVALID
        if end is None:
            return operand.find(sub, int(start))  # type: ignore[arg-type]
        return operand.find(sub, int(start), int(end))  # type: ignore[arg-type]


class BytesCountOp(BinaryQuery[int]):
    """Count sub-bytes occurrences: bytes.count(sub)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.count(right)


# =============================================================================
# PREFIX/SUFFIX TESTING
# =============================================================================


class BytesStartsWithOp(BinaryQuery[bool]):
    """Check if starts with prefix: bytes.startswith(prefix)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.startswith(right)


class BytesEndsWithOp(BinaryQuery[bool]):
    """Check if ends with suffix: bytes.endswith(suffix)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.endswith(right)


# =============================================================================
# REPLACING
# =============================================================================


class BytesReplaceOp(ScalarQuery[bytes]):
    """Replace sub-bytes: bytes.replace(old, new, count)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

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
