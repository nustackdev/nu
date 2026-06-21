"""Bytes-specific interactions.

Decoding: DecodeQuery, HexQuery
Case transformation: BytesUpperQuery, BytesLowerQuery
Stripping: BytesStripQuery, BytesLStripQuery, BytesRStripQuery
Splitting: BytesSplitQuery
Searching: BytesFindQuery, BytesCountQuery
Testing: BytesStartsWithQuery, BytesEndsWithQuery
Replacing: BytesReplaceQuery
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "BytesCountQuery",
    "BytesEndsWithQuery",
    "BytesFindQuery",
    "BytesLStripQuery",
    "BytesLowerQuery",
    "BytesRStripQuery",
    "BytesReplaceQuery",
    "BytesSplitQuery",
    "BytesStartsWithQuery",
    "BytesStripQuery",
    "BytesUpperQuery",
    "DecodeQuery",
    "HexQuery",
]


# =============================================================================
# DECODING
# =============================================================================


class DecodeQuery(ScalarQuery):
    """Decode bytes to string: bytes.decode(encoding)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes):
                return INVALID
            try:
                return left.decode(str(right))
            except (UnicodeDecodeError, LookupError):
                return INVALID

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes):
                return INVALID
            try:
                return left.decode(str(right))
            except (UnicodeDecodeError, LookupError):
                return INVALID

        return athunk


class HexQuery(ScalarQuery):
    """Convert to hex string: bytes.hex()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.hex()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.hex()

        return athunk


# =============================================================================
# CASE TRANSFORMATION
# =============================================================================


class BytesUpperQuery(ScalarQuery):
    """Convert to uppercase: bytes.upper()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.upper()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.upper()

        return athunk


class BytesLowerQuery(ScalarQuery):
    """Convert to lowercase: bytes.lower()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.lower()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.lower()

        return athunk


# =============================================================================
# STRIPPING
# =============================================================================


class BytesStripQuery(ScalarQuery):
    """Strip bytes: bytes.strip(chars)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes):
                return INVALID
            if right is not None and not isinstance(right, bytes):
                return INVALID
            return left.strip(right)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes):
                return INVALID
            if right is not None and not isinstance(right, bytes):
                return INVALID
            return left.strip(right)

        return athunk


class BytesLStripQuery(ScalarQuery):
    """Strip leading bytes: bytes.lstrip(chars)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes):
                return INVALID
            if right is not None and not isinstance(right, bytes):
                return INVALID
            return left.lstrip(right)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes):
                return INVALID
            if right is not None and not isinstance(right, bytes):
                return INVALID
            return left.lstrip(right)

        return athunk


class BytesRStripQuery(ScalarQuery):
    """Strip trailing bytes: bytes.rstrip(chars)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes):
                return INVALID
            if right is not None and not isinstance(right, bytes):
                return INVALID
            return left.rstrip(right)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes):
                return INVALID
            if right is not None and not isinstance(right, bytes):
                return INVALID
            return left.rstrip(right)

        return athunk


# =============================================================================
# SPLITTING
# =============================================================================


class BytesSplitQuery(ScalarQuery):
    """Split bytes: bytes.split(sep, maxsplit)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        first_t, second_t, third_t = children

        def thunk(rt: Runtime) -> object:
            first = first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            second = second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            third = third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            if not isinstance(first, bytes):
                return INVALID
            if second is not None and not isinstance(second, bytes):
                return INVALID
            return first.split(second, int(third))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        first_t, second_t, third_t = children

        async def athunk(rt: Runtime) -> object:
            first = await first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            second = await second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            third = await third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            if not isinstance(first, bytes):
                return INVALID
            if second is not None and not isinstance(second, bytes):
                return INVALID
            return first.split(second, int(third))

        return athunk


# =============================================================================
# SEARCHING
# =============================================================================


class BytesFindQuery(ScalarQuery):
    """Find sub-bytes: bytes.find(sub, start, end)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        operand_t, sub_t, start_t, end_t = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            sub = sub_t(rt)
            if sub is EMPTY or sub is INVALID:
                return INVALID
            start = start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = end_t(rt)
            if end is EMPTY or end is INVALID:
                return INVALID
            if not isinstance(operand, bytes) or not isinstance(sub, bytes):
                return INVALID
            if end is None:
                return operand.find(sub, int(start))
            return operand.find(sub, int(start), int(end))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        operand_t, sub_t, start_t, end_t = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            sub = await sub_t(rt)
            if sub is EMPTY or sub is INVALID:
                return INVALID
            start = await start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = await end_t(rt)
            if end is EMPTY or end is INVALID:
                return INVALID
            if not isinstance(operand, bytes) or not isinstance(sub, bytes):
                return INVALID
            if end is None:
                return operand.find(sub, int(start))
            return operand.find(sub, int(start), int(end))

        return athunk


class BytesCountQuery(ScalarQuery):
    """Count sub-bytes occurrences: bytes.count(sub)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, bytes):
                return INVALID
            return left.count(right)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, bytes):
                return INVALID
            return left.count(right)

        return athunk


# =============================================================================
# PREFIX/SUFFIX TESTING
# =============================================================================


class BytesStartsWithQuery(ScalarQuery):
    """Check if starts with prefix: bytes.startswith(prefix)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, bytes):
                return INVALID
            return left.startswith(right)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, bytes):
                return INVALID
            return left.startswith(right)

        return athunk


class BytesEndsWithQuery(ScalarQuery):
    """Check if ends with suffix: bytes.endswith(suffix)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, bytes):
                return INVALID
            return left.endswith(right)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, bytes):
                return INVALID
            return left.endswith(right)

        return athunk


# =============================================================================
# REPLACING
# =============================================================================


class BytesReplaceQuery(ScalarQuery):
    """Replace sub-bytes: bytes.replace(old, new, count)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        operand_t, old_t, new_t, count_t = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            old = old_t(rt)
            if old is EMPTY or old is INVALID:
                return INVALID
            new = new_t(rt)
            if new is EMPTY or new is INVALID:
                return INVALID
            count = count_t(rt)
            if count is EMPTY or count is INVALID:
                return INVALID
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

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        operand_t, old_t, new_t, count_t = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            old = await old_t(rt)
            if old is EMPTY or old is INVALID:
                return INVALID
            new = await new_t(rt)
            if new is EMPTY or new is INVALID:
                return INVALID
            count = await count_t(rt)
            if count is EMPTY or count is INVALID:
                return INVALID
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

        return athunk
