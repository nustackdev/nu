"""Bytes-specific interactions.

bytes is immutable, so every interaction here is a Query (returns a new value,
mutates nothing).

Decoding: Decode, Hex
Case transformation: BytesUpper, BytesLower, BytesTitle,
    BytesCapitalize, BytesSwapCase
Stripping: BytesStrip, BytesLStrip, BytesRStrip
Splitting: BytesSplit, BytesRSplit, BytesSplitLines,
    BytesPartition, BytesRPartition
Searching: BytesFind, BytesRFind, BytesIndex, BytesRIndex,
    BytesCount
Testing: BytesStartsWith, BytesEndsWith
Predicates: BytesIsAscii, BytesIsDigit, BytesIsAlpha,
    BytesIsAlnum, BytesIsSpace, BytesIsTitle, BytesIsUpper,
    BytesIsLower
Justifying: BytesCenter, BytesLJust, BytesRJust, BytesZFill
Replacing: BytesReplace, BytesRemovePrefix, BytesRemoveSuffix,
    BytesTranslate
Tabs: BytesExpandTabs
Joining: BytesJoin
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "BytesCapitalize",
    "BytesCenter",
    "BytesCount",
    "BytesEndsWith",
    "BytesExpandTabs",
    "BytesFind",
    "BytesIndex",
    "BytesIsAlnum",
    "BytesIsAlpha",
    "BytesIsAscii",
    "BytesIsDigit",
    "BytesIsLower",
    "BytesIsSpace",
    "BytesIsTitle",
    "BytesIsUpper",
    "BytesJoin",
    "BytesLJust",
    "BytesLStrip",
    "BytesLower",
    "BytesPartition",
    "BytesRFind",
    "BytesRIndex",
    "BytesRJust",
    "BytesRPartition",
    "BytesRSplit",
    "BytesRStrip",
    "BytesRemovePrefix",
    "BytesRemoveSuffix",
    "BytesReplace",
    "BytesSplit",
    "BytesSplitLines",
    "BytesStartsWith",
    "BytesStrip",
    "BytesSwapCase",
    "BytesTitle",
    "BytesTranslate",
    "BytesUpper",
    "BytesZFill",
    "Decode",
    "Hex",
]


# =============================================================================
# DECODING
# =============================================================================


class Decode(ScalarQuery):
    """Decode bytes to string: bytes.decode(encoding)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
                return left.decode(right)
            except (UnicodeDecodeError, LookupError):
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
                return left.decode(right)
            except (UnicodeDecodeError, LookupError):
                return INVALID

        return athunk


class Hex(ScalarQuery):
    """Convert to hex string: bytes.hex()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.hex()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesUpper(ScalarQuery):
    """Convert to uppercase: bytes.upper()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.upper()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.upper()

        return athunk


class BytesLower(ScalarQuery):
    """Convert to lowercase: bytes.lower()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.lower()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesStrip(ScalarQuery):
    """Strip bytes: bytes.strip(chars)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesLStrip(ScalarQuery):
    """Strip leading bytes: bytes.lstrip(chars)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesRStrip(ScalarQuery):
    """Strip trailing bytes: bytes.rstrip(chars)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesSplit(ScalarQuery):
    """Split bytes: bytes.split(sep, maxsplit)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesFind(ScalarQuery):
    """Find sub-bytes: bytes.find(sub, start, end)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesCount(ScalarQuery):
    """Count sub-bytes occurrences: bytes.count(sub)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesStartsWith(ScalarQuery):
    """Check if starts with prefix: bytes.startswith(prefix)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesEndsWith(ScalarQuery):
    """Check if ends with suffix: bytes.endswith(suffix)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesReplace(ScalarQuery):
    """Replace sub-bytes: bytes.replace(old, new, count)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class BytesRemovePrefix(ScalarQuery):
    """Remove a prefix: bytes.removeprefix(prefix)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            return left.removeprefix(right)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            return left.removeprefix(right)

        return athunk


class BytesRemoveSuffix(ScalarQuery):
    """Remove a suffix: bytes.removesuffix(suffix)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            return left.removesuffix(right)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            return left.removesuffix(right)

        return athunk


class BytesTranslate(ScalarQuery):
    """Translate via a 256-length table: bytes.translate(table, delete)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand_t, table_t, delete_t = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            table = table_t(rt)
            if table is EMPTY or table is INVALID:
                return INVALID
            delete = delete_t(rt)
            if delete is EMPTY or delete is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            if table is not None and not isinstance(table, bytes):
                return INVALID
            if not isinstance(delete, bytes):
                return INVALID
            try:
                return operand.translate(table, delete)
            except ValueError:
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand_t, table_t, delete_t = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            table = await table_t(rt)
            if table is EMPTY or table is INVALID:
                return INVALID
            delete = await delete_t(rt)
            if delete is EMPTY or delete is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            if table is not None and not isinstance(table, bytes):
                return INVALID
            if not isinstance(delete, bytes):
                return INVALID
            try:
                return operand.translate(table, delete)
            except ValueError:
                return INVALID

        return athunk


# =============================================================================
# CASE TRANSFORMATION (extra)
# =============================================================================


class BytesTitle(ScalarQuery):
    """Titlecase bytes: bytes.title()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.title()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.title()

        return athunk


class BytesCapitalize(ScalarQuery):
    """Capitalize bytes: bytes.capitalize()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.capitalize()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.capitalize()

        return athunk


class BytesSwapCase(ScalarQuery):
    """Swap case of bytes: bytes.swapcase()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.swapcase()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.swapcase()

        return athunk


# =============================================================================
# SPLITTING (extra)
# =============================================================================


class BytesRSplit(ScalarQuery):
    """Split bytes from the right: bytes.rsplit(sep, maxsplit)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            return first.rsplit(second, int(third))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            return first.rsplit(second, int(third))

        return athunk


class BytesSplitLines(ScalarQuery):
    """Split on line boundaries: bytes.splitlines(keepends)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            return left.splitlines(bool(right))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            return left.splitlines(bool(right))

        return athunk


class BytesPartition(ScalarQuery):
    """Partition on first occurrence: bytes.partition(sep)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            try:
                return left.partition(right)
            except ValueError:
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            try:
                return left.partition(right)
            except ValueError:
                return INVALID

        return athunk


class BytesRPartition(ScalarQuery):
    """Partition on last occurrence: bytes.rpartition(sep)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            try:
                return left.rpartition(right)
            except ValueError:
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            try:
                return left.rpartition(right)
            except ValueError:
                return INVALID

        return athunk


# =============================================================================
# SEARCHING (extra)
# =============================================================================


class BytesRFind(ScalarQuery):
    """Find sub-bytes from the right: bytes.rfind(sub, start, end)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
                return operand.rfind(sub, int(start))
            return operand.rfind(sub, int(start), int(end))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
                return operand.rfind(sub, int(start))
            return operand.rfind(sub, int(start), int(end))

        return athunk


class BytesIndex(ScalarQuery):
    """Index of sub-bytes (ValueError if absent): bytes.index(sub, start, end)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            try:
                if end is None:
                    return operand.index(sub, int(start))
                return operand.index(sub, int(start), int(end))
            except ValueError:
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            try:
                if end is None:
                    return operand.index(sub, int(start))
                return operand.index(sub, int(start), int(end))
            except ValueError:
                return INVALID

        return athunk


class BytesRIndex(ScalarQuery):
    """Index of sub-bytes from the right (ValueError if absent): bytes.rindex(sub, start, end)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            try:
                if end is None:
                    return operand.rindex(sub, int(start))
                return operand.rindex(sub, int(start), int(end))
            except ValueError:
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            try:
                if end is None:
                    return operand.rindex(sub, int(start))
                return operand.rindex(sub, int(start), int(end))
            except ValueError:
                return INVALID

        return athunk


# =============================================================================
# PREDICATES
# =============================================================================


class BytesIsAscii(ScalarQuery):
    """Test all bytes are ASCII: bytes.isascii()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isascii()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isascii()

        return athunk


class BytesIsDigit(ScalarQuery):
    """Test all bytes are ASCII digits: bytes.isdigit()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isdigit()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isdigit()

        return athunk


class BytesIsAlpha(ScalarQuery):
    """Test all bytes are ASCII letters: bytes.isalpha()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isalpha()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isalpha()

        return athunk


class BytesIsAlnum(ScalarQuery):
    """Test all bytes are ASCII alphanumeric: bytes.isalnum()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isalnum()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isalnum()

        return athunk


class BytesIsSpace(ScalarQuery):
    """Test all bytes are ASCII whitespace: bytes.isspace()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isspace()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isspace()

        return athunk


class BytesIsTitle(ScalarQuery):
    """Test bytes are titlecased: bytes.istitle()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.istitle()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.istitle()

        return athunk


class BytesIsUpper(ScalarQuery):
    """Test bytes are uppercase: bytes.isupper()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isupper()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.isupper()

        return athunk


class BytesIsLower(ScalarQuery):
    """Test bytes are lowercase: bytes.islower()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.islower()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand_t,) = children

        async def athunk(rt: Runtime) -> object:
            operand = await operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            if not isinstance(operand, bytes):
                return INVALID
            return operand.islower()

        return athunk


# =============================================================================
# JUSTIFYING
# =============================================================================


class BytesCenter(ScalarQuery):
    """Center in width: bytes.center(width, fillbyte)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            if not isinstance(first, bytes) or not isinstance(second, int):
                return INVALID
            if not isinstance(third, bytes) or len(third) != 1:
                return INVALID
            return first.center(second, third)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            if not isinstance(first, bytes) or not isinstance(second, int):
                return INVALID
            if not isinstance(third, bytes) or len(third) != 1:
                return INVALID
            return first.center(second, third)

        return athunk


class BytesLJust(ScalarQuery):
    """Left justify: bytes.ljust(width, fillbyte)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            if not isinstance(first, bytes) or not isinstance(second, int):
                return INVALID
            if not isinstance(third, bytes) or len(third) != 1:
                return INVALID
            return first.ljust(second, third)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            if not isinstance(first, bytes) or not isinstance(second, int):
                return INVALID
            if not isinstance(third, bytes) or len(third) != 1:
                return INVALID
            return first.ljust(second, third)

        return athunk


class BytesRJust(ScalarQuery):
    """Right justify: bytes.rjust(width, fillbyte)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            if not isinstance(first, bytes) or not isinstance(second, int):
                return INVALID
            if not isinstance(third, bytes) or len(third) != 1:
                return INVALID
            return first.rjust(second, third)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
            if not isinstance(first, bytes) or not isinstance(second, int):
                return INVALID
            if not isinstance(third, bytes) or len(third) != 1:
                return INVALID
            return first.rjust(second, third)

        return athunk


class BytesZFill(ScalarQuery):
    """Zero-fill: bytes.zfill(width)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, int):
                return INVALID
            return left.zfill(right)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, int):
                return INVALID
            return left.zfill(right)

        return athunk


# =============================================================================
# TABS
# =============================================================================


class BytesExpandTabs(ScalarQuery):
    """Expand tabs to spaces: bytes.expandtabs(tabsize)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, int):
                return INVALID
            return left.expandtabs(right)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, bytes) or not isinstance(right, int):
                return INVALID
            return left.expandtabs(right)

        return athunk


# =============================================================================
# JOINING
# =============================================================================


class BytesJoin(ScalarQuery):
    """Join an iterable of bytes: sep.join(seq)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
                return left.join(right)
            except TypeError:
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
                return left.join(right)
            except TypeError:
                return INVALID

        return athunk
