"""Bytes operations for Term expressions.

This module provides type-safe operations on bytes Terms:

Decoding: DecodeOp, HexOp
Case transformation: BytesUpperOp, BytesLowerOp
Stripping: BytesStripOp, BytesLStripOp, BytesRStripOp
Splitting: BytesSplitOp
Searching: BytesFindOp, BytesCountOp
Testing: BytesStartsWithOp, BytesEndsWithOp
Replacing: BytesReplaceOp

Design principles:
1. Atomic classes: one operation = one class
2. All arguments support Term or literal
3. Proper base class inheritance (UnaryOp, BinaryOp, NAryOp)
4. Runtime type checking with INVALID for invalid types
"""

from __future__ import annotations

from everyterm.term import BinaryOp, NAryOp, UnaryOp
from everyterm.typing import INVALID, NOT_SET, NotSet, Sentinel, is_notset


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
# DECODING (Binary - operand and encoding as Terms)
# =============================================================================


class DecodeOp(BinaryOp[str | Sentinel]):
    """Decode bytes to string: bytes.decode(encoding)."""

    def _apply_op(self, operand: object, encoding: object) -> str | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        try:
            return operand.decode(str(encoding) if encoding else "utf-8")
        except (UnicodeDecodeError, LookupError):
            return INVALID


class HexOp(UnaryOp[str | Sentinel]):
    """Convert to hex string: bytes.hex()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        return operand.hex()


# =============================================================================
# CASE TRANSFORMATION (Unary)
# =============================================================================


class BytesUpperOp(UnaryOp[bytes | Sentinel]):
    """Convert to uppercase: bytes.upper()."""

    def _apply_op(self, operand: object) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        return operand.upper()


class BytesLowerOp(UnaryOp[bytes | Sentinel]):
    """Convert to lowercase: bytes.lower()."""

    def _apply_op(self, operand: object) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        return operand.lower()


# =============================================================================
# STRIPPING (NAryOp - optional chars argument)
# =============================================================================


class BytesStripOp(NAryOp[bytes | Sentinel]):
    """Strip bytes: bytes.strip(chars).

    Args can be Terms for dynamic values.
    """

    def __init__(self, operand: object, chars: object | NotSet = NOT_SET) -> None:
        """Initialize strip operation."""
        if is_notset(chars):
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply_op(self, operand: object, chars: object = NOT_SET) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        if is_notset(chars):
            return operand.strip()
        if chars is not None and not isinstance(chars, bytes):
            return INVALID
        return operand.strip(chars)


class BytesLStripOp(NAryOp[bytes | Sentinel]):
    """Strip leading bytes: bytes.lstrip(chars)."""

    def __init__(self, operand: object, chars: object | NotSet = NOT_SET) -> None:
        """Initialize lstrip operation."""
        if is_notset(chars):
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply_op(self, operand: object, chars: object = NOT_SET) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        if is_notset(chars):
            return operand.lstrip()
        if chars is not None and not isinstance(chars, bytes):
            return INVALID
        return operand.lstrip(chars)


class BytesRStripOp(NAryOp[bytes | Sentinel]):
    """Strip trailing bytes: bytes.rstrip(chars)."""

    def __init__(self, operand: object, chars: object | NotSet = NOT_SET) -> None:
        """Initialize rstrip operation."""
        if is_notset(chars):
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply_op(self, operand: object, chars: object = NOT_SET) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        if is_notset(chars):
            return operand.rstrip()
        if chars is not None and not isinstance(chars, bytes):
            return INVALID
        return operand.rstrip(chars)


# =============================================================================
# SPLITTING (NAryOp - optional sep, maxsplit as Terms)
# =============================================================================


class BytesSplitOp(NAryOp[list[bytes] | Sentinel]):
    """Split bytes: bytes.split(sep, maxsplit).

    All args can be Terms for dynamic values.
    """

    def __init__(
        self,
        operand: object,
        sep: object | NotSet = NOT_SET,
        maxsplit: object = -1,
    ) -> None:
        """Initialize split operation."""
        if is_notset(sep):
            super().__init__(operand, maxsplit)
            self._has_sep = False
        else:
            super().__init__(operand, sep, maxsplit)
            self._has_sep = True

    def _apply_op(self, *args: object) -> list[bytes] | Sentinel:
        if self._has_sep:
            operand, sep, maxsplit = args
        else:
            operand, maxsplit = args
            sep = None

        if not isinstance(operand, bytes):
            return INVALID
        if sep is not None and not isinstance(sep, bytes):
            return INVALID
        return operand.split(sep, int(maxsplit))  # type: ignore[arg-type]


# =============================================================================
# SEARCHING (NAryOp for optional start/end, Binary for simple)
# =============================================================================


class BytesFindOp(NAryOp[int | Sentinel]):
    """Find sub-bytes: bytes.find(sub, start, end).

    All args can be Terms.
    """

    def __init__(
        self,
        operand: object,
        sub: object,
        start: object = 0,
        end: object | NotSet = NOT_SET,
    ) -> None:
        """Initialize find operation."""
        if is_notset(end):
            super().__init__(operand, sub, start)
        else:
            super().__init__(operand, sub, start, end)

    def _apply_op(
        self, operand: object, sub: object, start: object, end: object = NOT_SET
    ) -> int | Sentinel:
        if not isinstance(operand, bytes) or not isinstance(sub, bytes):
            return INVALID
        if is_notset(end) or end is None:
            return operand.find(sub, int(start))  # type: ignore[arg-type]
        return operand.find(sub, int(start), int(end))  # type: ignore[arg-type]


class BytesCountOp(BinaryOp[int | Sentinel]):
    """Count sub-bytes occurrences: bytes.count(sub)."""

    def _apply_op(self, operand: object, sub: object) -> int | Sentinel:
        if not isinstance(operand, bytes) or not isinstance(sub, bytes):
            return INVALID
        return operand.count(sub)


# =============================================================================
# PREFIX/SUFFIX TESTING (Binary)
# =============================================================================


class BytesStartsWithOp(BinaryOp[bool | Sentinel]):
    """Check if starts with prefix: bytes.startswith(prefix)."""

    def _apply_op(self, operand: object, prefix: object) -> bool | Sentinel:
        if not isinstance(operand, bytes) or not isinstance(prefix, bytes):
            return INVALID
        return operand.startswith(prefix)


class BytesEndsWithOp(BinaryOp[bool | Sentinel]):
    """Check if ends with suffix: bytes.endswith(suffix)."""

    def _apply_op(self, operand: object, suffix: object) -> bool | Sentinel:
        if not isinstance(operand, bytes) or not isinstance(suffix, bytes):
            return INVALID
        return operand.endswith(suffix)


# =============================================================================
# REPLACING (NAryOp - operand, old, new, count all as Terms)
# =============================================================================


class BytesReplaceOp(NAryOp[bytes | Sentinel]):
    """Replace sub-bytes: bytes.replace(old, new, count).

    All args can be Terms.
    """

    def __init__(
        self,
        operand: object,
        old: object,
        new: object,
        count: object = -1,
    ) -> None:
        """Initialize replace operation."""
        super().__init__(operand, old, new, count)

    def _apply_op(
        self, operand: object, old: object, new: object, count: object
    ) -> bytes | Sentinel:
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
