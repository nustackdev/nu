"""Bytes-specific morphisms.

Decoding: DecodeOp, HexOp
Case transformation: BytesUpperOp, BytesLowerOp
Stripping: BytesStripOp, BytesLStripOp, BytesRStripOp
Splitting: BytesSplitOp
Searching: BytesFindOp, BytesCountOp
Testing: BytesStartsWithOp, BytesEndsWithOp
Replacing: BytesReplaceOp

All ops use every.Morphism base classes with Operation mixin (pure).
"""

from __future__ import annotations

from everyabc import (
    INVALID,
    BinaryMorphism,
    NAryMorphism,
    Operation,
    Sentinel,
    UnaryMorphism,
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


class DecodeOp(Operation, BinaryMorphism[str | Sentinel]):
    """Decode bytes to string: bytes.decode(encoding)."""

    def _apply(self, operand: object, encoding: object) -> str | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        try:
            return operand.decode(str(encoding) if encoding else "utf-8")
        except (UnicodeDecodeError, LookupError):
            return INVALID


class HexOp(Operation, UnaryMorphism[str | Sentinel]):
    """Convert to hex string: bytes.hex()."""

    def _apply(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        return operand.hex()


# =============================================================================
# CASE TRANSFORMATION
# =============================================================================


class BytesUpperOp(Operation, UnaryMorphism[bytes | Sentinel]):
    """Convert to uppercase: bytes.upper()."""

    def _apply(self, operand: object) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        return operand.upper()


class BytesLowerOp(Operation, UnaryMorphism[bytes | Sentinel]):
    """Convert to lowercase: bytes.lower()."""

    def _apply(self, operand: object) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return INVALID
        return operand.lower()


# =============================================================================
# STRIPPING
# =============================================================================


class BytesStripOp(Operation, NAryMorphism[bytes | Sentinel]):
    """Strip bytes: bytes.strip(chars)."""

    def __init__(self, operand: object, chars: object | None = None) -> None:
        """Initialize strip operation."""
        if chars is None:
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply(self, *args: object) -> bytes | Sentinel:
        if len(args) == 1:
            operand = args[0]
            chars = None
        else:
            operand, chars = args

        if not isinstance(operand, bytes):
            return INVALID
        if chars is not None and not isinstance(chars, bytes):
            return INVALID
        return operand.strip(chars)


class BytesLStripOp(Operation, NAryMorphism[bytes | Sentinel]):
    """Strip leading bytes: bytes.lstrip(chars)."""

    def __init__(self, operand: object, chars: object | None = None) -> None:
        """Initialize lstrip operation."""
        if chars is None:
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply(self, *args: object) -> bytes | Sentinel:
        if len(args) == 1:
            operand = args[0]
            chars = None
        else:
            operand, chars = args

        if not isinstance(operand, bytes):
            return INVALID
        if chars is not None and not isinstance(chars, bytes):
            return INVALID
        return operand.lstrip(chars)


class BytesRStripOp(Operation, NAryMorphism[bytes | Sentinel]):
    """Strip trailing bytes: bytes.rstrip(chars)."""

    def __init__(self, operand: object, chars: object | None = None) -> None:
        """Initialize rstrip operation."""
        if chars is None:
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply(self, *args: object) -> bytes | Sentinel:
        if len(args) == 1:
            operand = args[0]
            chars = None
        else:
            operand, chars = args

        if not isinstance(operand, bytes):
            return INVALID
        if chars is not None and not isinstance(chars, bytes):
            return INVALID
        return operand.rstrip(chars)


# =============================================================================
# SPLITTING
# =============================================================================


class BytesSplitOp(Operation, NAryMorphism[list[bytes] | Sentinel]):
    """Split bytes: bytes.split(sep, maxsplit)."""

    _has_sep: bool

    def __init__(
        self,
        operand: object,
        sep: object | None = None,
        maxsplit: object = -1,
    ) -> None:
        """Initialize split operation."""
        if sep is None:
            super().__init__(operand, maxsplit)
            self._has_sep = False
        else:
            super().__init__(operand, sep, maxsplit)
            self._has_sep = True

    def _apply(self, *args: object) -> list[bytes] | Sentinel:
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
# SEARCHING
# =============================================================================


class BytesFindOp(Operation, NAryMorphism[int | Sentinel]):
    """Find sub-bytes: bytes.find(sub, start, end)."""

    def __init__(
        self,
        operand: object,
        sub: object,
        start: object = 0,
        end: object | None = None,
    ) -> None:
        """Initialize find operation."""
        if end is None:
            super().__init__(operand, sub, start)
        else:
            super().__init__(operand, sub, start, end)

    def _apply(self, *args: object) -> int | Sentinel:
        if len(args) == 3:
            operand, sub, start = args
            end = None
        else:
            operand, sub, start, end = args

        if not isinstance(operand, bytes) or not isinstance(sub, bytes):
            return INVALID
        if end is None:
            return operand.find(sub, int(start))  # type: ignore[arg-type]
        return operand.find(sub, int(start), int(end))  # type: ignore[arg-type]


class BytesCountOp(Operation, BinaryMorphism[int | Sentinel]):
    """Count sub-bytes occurrences: bytes.count(sub)."""

    def _apply(self, operand: object, sub: object) -> int | Sentinel:
        if not isinstance(operand, bytes) or not isinstance(sub, bytes):
            return INVALID
        return operand.count(sub)


# =============================================================================
# PREFIX/SUFFIX TESTING
# =============================================================================


class BytesStartsWithOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Check if starts with prefix: bytes.startswith(prefix)."""

    def _apply(self, operand: object, prefix: object) -> bool | Sentinel:
        if not isinstance(operand, bytes) or not isinstance(prefix, bytes):
            return INVALID
        return operand.startswith(prefix)


class BytesEndsWithOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Check if ends with suffix: bytes.endswith(suffix)."""

    def _apply(self, operand: object, suffix: object) -> bool | Sentinel:
        if not isinstance(operand, bytes) or not isinstance(suffix, bytes):
            return INVALID
        return operand.endswith(suffix)


# =============================================================================
# REPLACING
# =============================================================================


class BytesReplaceOp(Operation, NAryMorphism[bytes | Sentinel]):
    """Replace sub-bytes: bytes.replace(old, new, count)."""

    def __init__(
        self,
        operand: object,
        old: object,
        new: object,
        count: object = -1,
    ) -> None:
        """Initialize replace operation."""
        super().__init__(operand, old, new, count)

    def _apply(self, operand: object, old: object, new: object, count: object) -> bytes | Sentinel:
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
