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

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


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


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# DECODING
# =============================================================================


class DecodeOp(ScalarQuery):
    """Decode bytes to string: bytes.decode(encoding)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, bytes):
            return INVALID
        try:
            return left.decode(str(right))
        except (UnicodeDecodeError, LookupError):
            return INVALID


class HexOp(ScalarQuery):
    """Convert to hex string: bytes.hex()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, bytes):
            return INVALID
        return operand.hex()


# =============================================================================
# CASE TRANSFORMATION
# =============================================================================


class BytesUpperOp(ScalarQuery):
    """Convert to uppercase: bytes.upper()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, bytes):
            return INVALID
        return operand.upper()


class BytesLowerOp(ScalarQuery):
    """Convert to lowercase: bytes.lower()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, bytes):
            return INVALID
        return operand.lower()


# =============================================================================
# STRIPPING
# =============================================================================


class BytesStripOp(ScalarQuery):
    """Strip bytes: bytes.strip(chars)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, bytes):
            return INVALID
        if right is not None and not isinstance(right, bytes):
            return INVALID
        return left.strip(right)


class BytesLStripOp(ScalarQuery):
    """Strip leading bytes: bytes.lstrip(chars)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, bytes):
            return INVALID
        if right is not None and not isinstance(right, bytes):
            return INVALID
        return left.lstrip(right)


class BytesRStripOp(ScalarQuery):
    """Strip trailing bytes: bytes.rstrip(chars)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, bytes):
            return INVALID
        if right is not None and not isinstance(right, bytes):
            return INVALID
        return left.rstrip(right)


# =============================================================================
# SPLITTING
# =============================================================================


class BytesSplitOp(ScalarQuery):
    """Split bytes: bytes.split(sep, maxsplit)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        first, second, third = ops
        if not isinstance(first, bytes):
            return INVALID
        if second is not None and not isinstance(second, bytes):
            return INVALID
        return first.split(second, int(third))


# =============================================================================
# SEARCHING
# =============================================================================


class BytesFindOp(ScalarQuery):
    """Find sub-bytes: bytes.find(sub, start, end)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any, d: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c, d)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand, sub, start, end = ops
        if not isinstance(operand, bytes) or not isinstance(sub, bytes):
            return INVALID
        if end is None:
            return operand.find(sub, int(start))
        return operand.find(sub, int(start), int(end))


class BytesCountOp(ScalarQuery):
    """Count sub-bytes occurrences: bytes.count(sub)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.count(right)


# =============================================================================
# PREFIX/SUFFIX TESTING
# =============================================================================


class BytesStartsWithOp(ScalarQuery):
    """Check if starts with prefix: bytes.startswith(prefix)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.startswith(right)


class BytesEndsWithOp(ScalarQuery):
    """Check if ends with suffix: bytes.endswith(suffix)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            return INVALID
        return left.endswith(right)


# =============================================================================
# REPLACING
# =============================================================================


class BytesReplaceOp(ScalarQuery):
    """Replace sub-bytes: bytes.replace(old, new, count)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any, d: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c, d)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand, old, new, count = ops
        if (
            not isinstance(operand, bytes)
            or not isinstance(old, bytes)
            or not isinstance(new, bytes)
        ):
            return INVALID
        count_int = int(count)
        if count_int == -1:
            return operand.replace(old, new)
        return operand.replace(old, new, count_int)
