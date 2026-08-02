"""String-specific interactions.

All str methods are pure (str is immutable), so every interaction is a Query.

Case transformation: Upper, Lower, Title, Capitalize, SwapCase, Casefold
Stripping: Strip, LStrip, RStrip
Splitting: Split, RSplit, SplitLines, Partition, RPartition
Searching: Find, RFind, Index, RIndex, CountSubstring
Padding: Center, LJust, RJust, ZFill, ExpandTabs
Testing: StartsWith, EndsWith, IsDigit, IsAlpha, IsAlnum, IsSpace,
    IsNumeric, IsDecimal, IsIdentifier, IsPrintable, IsTitle, IsUpper,
    IsLower, IsAscii
Replacing: Replace, RemovePrefix, RemoveSuffix, Translate
Formatting: FormatMap
Encoding: Encode
Joining: Join
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "Capitalize",
    "Casefold",
    "Center",
    "CountSubstring",
    "Encode",
    "EndsWith",
    "ExpandTabs",
    "Find",
    "FormatMap",
    "Index",
    "IsAlnum",
    "IsAlpha",
    "IsAscii",
    "IsDecimal",
    "IsDigit",
    "IsIdentifier",
    "IsLower",
    "IsNumeric",
    "IsPrintable",
    "IsSpace",
    "IsTitle",
    "IsUpper",
    "Join",
    "LJust",
    "LStrip",
    "Lower",
    "Partition",
    "RFind",
    "RIndex",
    "RJust",
    "RPartition",
    "RSplit",
    "RStrip",
    "RemovePrefix",
    "RemoveSuffix",
    "Replace",
    "Split",
    "SplitLines",
    "StartsWith",
    "Strip",
    "SwapCase",
    "Title",
    "Translate",
    "Upper",
    "ZFill",
]


# =============================================================================
# CASE TRANSFORMATION (Unary)
# =============================================================================


class Upper(ScalarQuery):
    """Convert to uppercase: str.upper()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.upper()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.upper()

        return athunk


class Lower(ScalarQuery):
    """Convert to lowercase: str.lower()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.lower()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.lower()

        return athunk


class Title(ScalarQuery):
    """Convert to title case: str.title()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.title()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.title()

        return athunk


class Capitalize(ScalarQuery):
    """Capitalize first character: str.capitalize()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.capitalize()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.capitalize()

        return athunk


class SwapCase(ScalarQuery):
    """Swap case: str.swapcase()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.swapcase()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.swapcase()

        return athunk


# =============================================================================
# STRING TESTS (Unary)
# =============================================================================


class IsDigit(ScalarQuery):
    """Check if all digits: str.isdigit()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isdigit()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isdigit()

        return athunk


class IsAlpha(ScalarQuery):
    """Check if all alphabetic: str.isalpha()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isalpha()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isalpha()

        return athunk


class IsAlnum(ScalarQuery):
    """Check if alphanumeric: str.isalnum()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isalnum()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isalnum()

        return athunk


class IsSpace(ScalarQuery):
    """Check if all whitespace: str.isspace()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isspace()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isspace()

        return athunk


# =============================================================================
# STRIPPING (Binary)
# =============================================================================


class Strip(ScalarQuery):
    """Strip whitespace or chars: str.strip(chars)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if right is not None and not isinstance(right, str):
                return INVALID
            return left.strip(right)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if right is not None and not isinstance(right, str):
                return INVALID
            return left.strip(right)

        return athunk


class LStrip(ScalarQuery):
    """Strip leading whitespace or chars: str.lstrip(chars)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if right is not None and not isinstance(right, str):
                return INVALID
            return left.lstrip(right)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if right is not None and not isinstance(right, str):
                return INVALID
            return left.lstrip(right)

        return athunk


class RStrip(ScalarQuery):
    """Strip trailing whitespace or chars: str.rstrip(chars)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if right is not None and not isinstance(right, str):
                return INVALID
            return left.rstrip(right)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            right = await right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if right is not None and not isinstance(right, str):
                return INVALID
            return left.rstrip(right)

        return athunk


# =============================================================================
# SPLITTING (Ternary)
# =============================================================================


class Split(ScalarQuery):
    """Split string: str.split(sep, maxsplit)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        first_t, second_t, third_t = children

        def thunk(rt: Runtime) -> object:
            first = first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            if not isinstance(first, str):
                return INVALID
            second = second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            if second is not None and not isinstance(second, str):
                return INVALID
            third = third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            return first.split(second, int(third))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        first_t, second_t, third_t = children

        async def athunk(rt: Runtime) -> object:
            first = await first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            if not isinstance(first, str):
                return INVALID
            second = await second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            if second is not None and not isinstance(second, str):
                return INVALID
            third = await third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            return first.split(second, int(third))

        return athunk


class RSplit(ScalarQuery):
    """Right split string: str.rsplit(sep, maxsplit)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        first_t, second_t, third_t = children

        def thunk(rt: Runtime) -> object:
            first = first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            if not isinstance(first, str):
                return INVALID
            second = second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            if second is not None and not isinstance(second, str):
                return INVALID
            third = third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            return first.rsplit(second, int(third))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        first_t, second_t, third_t = children

        async def athunk(rt: Runtime) -> object:
            first = await first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            if not isinstance(first, str):
                return INVALID
            second = await second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            if second is not None and not isinstance(second, str):
                return INVALID
            third = await third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            return first.rsplit(second, int(third))

        return athunk


# =============================================================================
# SEARCHING
# =============================================================================


class Find(ScalarQuery):
    """Find substring: str.find(sub, start, end)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand_t, sub_t, start_t, end_t = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            sub = sub_t(rt)
            if sub is EMPTY or sub is INVALID:
                return INVALID
            if not isinstance(operand, str) or not isinstance(sub, str):
                return INVALID
            start = start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = end_t(rt)
            if end is EMPTY or end is INVALID:
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
            if not isinstance(operand, str) or not isinstance(sub, str):
                return INVALID
            start = await start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = await end_t(rt)
            if end is EMPTY or end is INVALID:
                return INVALID
            if end is None:
                return operand.find(sub, int(start))
            return operand.find(sub, int(start), int(end))

        return athunk


class RFind(ScalarQuery):
    """Find substring from right: str.rfind(sub, start, end)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand_t, sub_t, start_t, end_t = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            sub = sub_t(rt)
            if sub is EMPTY or sub is INVALID:
                return INVALID
            if not isinstance(operand, str) or not isinstance(sub, str):
                return INVALID
            start = start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = end_t(rt)
            if end is EMPTY or end is INVALID:
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
            if not isinstance(operand, str) or not isinstance(sub, str):
                return INVALID
            start = await start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = await end_t(rt)
            if end is EMPTY or end is INVALID:
                return INVALID
            if end is None:
                return operand.rfind(sub, int(start))
            return operand.rfind(sub, int(start), int(end))

        return athunk


class CountSubstring(ScalarQuery):
    """Count substring occurrences: str.count(sub)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, str):
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
            if not isinstance(left, str) or not isinstance(right, str):
                return INVALID
            return left.count(right)

        return athunk


# =============================================================================
# PREFIX/SUFFIX TESTING (Binary)
# =============================================================================


class StartsWith(ScalarQuery):
    """Check if starts with prefix: str.startswith(prefix)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, str):
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
            if not isinstance(left, str) or not isinstance(right, str):
                return INVALID
            return left.startswith(right)

        return athunk


class EndsWith(ScalarQuery):
    """Check if ends with suffix: str.endswith(suffix)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, str):
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
            if not isinstance(left, str) or not isinstance(right, str):
                return INVALID
            return left.endswith(right)

        return athunk


# =============================================================================
# PADDING (Ternary)
# =============================================================================


class Center(ScalarQuery):
    """Center in width: str.center(width, fillchar)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        first_t, second_t, third_t = children

        def thunk(rt: Runtime) -> object:
            first = first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            second = second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            if not isinstance(first, str) or not isinstance(second, int):
                return INVALID
            third = third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            if not isinstance(third, str):
                return INVALID
            try:
                return first.center(second, third)
            except TypeError:
                return INVALID

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
            if not isinstance(first, str) or not isinstance(second, int):
                return INVALID
            third = await third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            if not isinstance(third, str):
                return INVALID
            try:
                return first.center(second, third)
            except TypeError:
                return INVALID

        return athunk


class LJust(ScalarQuery):
    """Left justify: str.ljust(width, fillchar)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        first_t, second_t, third_t = children

        def thunk(rt: Runtime) -> object:
            first = first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            second = second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            if not isinstance(first, str) or not isinstance(second, int):
                return INVALID
            third = third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            if not isinstance(third, str):
                return INVALID
            try:
                return first.ljust(second, third)
            except TypeError:
                return INVALID

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
            if not isinstance(first, str) or not isinstance(second, int):
                return INVALID
            third = await third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            if not isinstance(third, str):
                return INVALID
            try:
                return first.ljust(second, third)
            except TypeError:
                return INVALID

        return athunk


class RJust(ScalarQuery):
    """Right justify: str.rjust(width, fillchar)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        first_t, second_t, third_t = children

        def thunk(rt: Runtime) -> object:
            first = first_t(rt)
            if first is EMPTY or first is INVALID:
                return INVALID
            second = second_t(rt)
            if second is EMPTY or second is INVALID:
                return INVALID
            if not isinstance(first, str) or not isinstance(second, int):
                return INVALID
            third = third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            if not isinstance(third, str):
                return INVALID
            try:
                return first.rjust(second, third)
            except TypeError:
                return INVALID

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
            if not isinstance(first, str) or not isinstance(second, int):
                return INVALID
            third = await third_t(rt)
            if third is EMPTY or third is INVALID:
                return INVALID
            if not isinstance(third, str):
                return INVALID
            try:
                return first.rjust(second, third)
            except TypeError:
                return INVALID

        return athunk


class ZFill(ScalarQuery):
    """Zero-fill: str.zfill(width)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, int):
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
            if not isinstance(left, str) or not isinstance(right, int):
                return INVALID
            return left.zfill(right)

        return athunk


# =============================================================================
# REPLACING
# =============================================================================


class Replace(ScalarQuery):
    """Replace substring: str.replace(old, new, count)."""

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
            if not isinstance(operand, str) or not isinstance(old, str) or not isinstance(new, str):
                return INVALID
            count = count_t(rt)
            if count is EMPTY or count is INVALID:
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
            if not isinstance(operand, str) or not isinstance(old, str) or not isinstance(new, str):
                return INVALID
            count = await count_t(rt)
            if count is EMPTY or count is INVALID:
                return INVALID
            count_int = int(count)
            if count_int == -1:
                return operand.replace(old, new)
            return operand.replace(old, new, count_int)

        return athunk


# =============================================================================
# ENCODING (Binary)
# =============================================================================


class Encode(ScalarQuery):
    """Encode string to bytes: str.encode(encoding)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            try:
                return left.encode(right)
            except (UnicodeEncodeError, LookupError):
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
            if not isinstance(left, str):
                return INVALID
            try:
                return left.encode(right)
            except (UnicodeEncodeError, LookupError):
                return INVALID

        return athunk


# =============================================================================
# JOINING
# =============================================================================


class Join(ScalarQuery):
    """Join iterable elements into string: sep.join(seq)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str):
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
            if not isinstance(left, str):
                return INVALID
            try:
                return left.join(right)
            except TypeError:
                return INVALID

        return athunk


# =============================================================================
# CASE TRANSFORMATION (Unary) - additions
# =============================================================================


class Casefold(ScalarQuery):
    """Casefold for caseless matching: str.casefold()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.casefold()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.casefold()

        return athunk


# =============================================================================
# STRING TESTS (Unary) - additions
# =============================================================================


class IsNumeric(ScalarQuery):
    """Check if all numeric: str.isnumeric()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isnumeric()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isnumeric()

        return athunk


class IsDecimal(ScalarQuery):
    """Check if all decimal: str.isdecimal()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isdecimal()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isdecimal()

        return athunk


class IsIdentifier(ScalarQuery):
    """Check if valid identifier: str.isidentifier()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isidentifier()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isidentifier()

        return athunk


class IsPrintable(ScalarQuery):
    """Check if all printable: str.isprintable()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isprintable()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isprintable()

        return athunk


class IsTitle(ScalarQuery):
    """Check if titlecased: str.istitle()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.istitle()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.istitle()

        return athunk


class IsUpper(ScalarQuery):
    """Check if all cased chars uppercase: str.isupper()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isupper()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isupper()

        return athunk


class IsLower(ScalarQuery):
    """Check if all cased chars lowercase: str.islower()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.islower()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.islower()

        return athunk


class IsAscii(ScalarQuery):
    """Check if all ASCII (empty is True): str.isascii()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isascii()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isascii()

        return athunk


# =============================================================================
# TABS (Binary)
# =============================================================================


class ExpandTabs(ScalarQuery):
    """Expand tabs to spaces: str.expandtabs(tabsize)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, int):
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
            if not isinstance(left, str) or not isinstance(right, int):
                return INVALID
            return left.expandtabs(right)

        return athunk


# =============================================================================
# PARTITION (Binary) - returns a 3-tuple
# =============================================================================


class Partition(ScalarQuery):
    """Split around first occurrence of sep: str.partition(sep)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, str):
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
            if not isinstance(left, str) or not isinstance(right, str):
                return INVALID
            try:
                return left.partition(right)
            except ValueError:
                return INVALID

        return athunk


class RPartition(ScalarQuery):
    """Split around last occurrence of sep: str.rpartition(sep)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, str):
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
            if not isinstance(left, str) or not isinstance(right, str):
                return INVALID
            try:
                return left.rpartition(right)
            except ValueError:
                return INVALID

        return athunk


# =============================================================================
# SPLITLINES (Binary) - returns a list
# =============================================================================


class SplitLines(ScalarQuery):
    """Split at line boundaries: str.splitlines(keepends)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str):
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
            if not isinstance(left, str):
                return INVALID
            return left.splitlines(bool(right))

        return athunk


# =============================================================================
# INDEX SEARCH (raises ValueError when not found)
# =============================================================================


class Index(ScalarQuery):
    """Find substring index, error if absent: str.index(sub, start, end)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand_t, sub_t, start_t, end_t = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            sub = sub_t(rt)
            if sub is EMPTY or sub is INVALID:
                return INVALID
            if not isinstance(operand, str) or not isinstance(sub, str):
                return INVALID
            start = start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = end_t(rt)
            if end is EMPTY or end is INVALID:
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
            if not isinstance(operand, str) or not isinstance(sub, str):
                return INVALID
            start = await start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = await end_t(rt)
            if end is EMPTY or end is INVALID:
                return INVALID
            try:
                if end is None:
                    return operand.index(sub, int(start))
                return operand.index(sub, int(start), int(end))
            except ValueError:
                return INVALID

        return athunk


class RIndex(ScalarQuery):
    """Find substring index from right, error if absent: str.rindex(sub, start, end)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand_t, sub_t, start_t, end_t = children

        def thunk(rt: Runtime) -> object:
            operand = operand_t(rt)
            if operand is EMPTY or operand is INVALID:
                return INVALID
            sub = sub_t(rt)
            if sub is EMPTY or sub is INVALID:
                return INVALID
            if not isinstance(operand, str) or not isinstance(sub, str):
                return INVALID
            start = start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = end_t(rt)
            if end is EMPTY or end is INVALID:
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
            if not isinstance(operand, str) or not isinstance(sub, str):
                return INVALID
            start = await start_t(rt)
            if start is EMPTY or start is INVALID:
                return INVALID
            end = await end_t(rt)
            if end is EMPTY or end is INVALID:
                return INVALID
            try:
                if end is None:
                    return operand.rindex(sub, int(start))
                return operand.rindex(sub, int(start), int(end))
            except ValueError:
                return INVALID

        return athunk


# =============================================================================
# PREFIX/SUFFIX REMOVAL (Binary)
# =============================================================================


class RemovePrefix(ScalarQuery):
    """Remove prefix if present: str.removeprefix(prefix)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, str):
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
            if not isinstance(left, str) or not isinstance(right, str):
                return INVALID
            return left.removeprefix(right)

        return athunk


class RemoveSuffix(ScalarQuery):
    """Remove suffix if present: str.removesuffix(suffix)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, right_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            right = right_t(rt)
            if right is EMPTY or right is INVALID:
                return INVALID
            if not isinstance(left, str) or not isinstance(right, str):
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
            if not isinstance(left, str) or not isinstance(right, str):
                return INVALID
            return left.removesuffix(right)

        return athunk


# =============================================================================
# TRANSLATE (Binary) - table is a value child (a mapping)
# =============================================================================


class Translate(ScalarQuery):
    """Map characters through a table: str.translate(table)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, table_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            table = table_t(rt)
            if table is EMPTY or table is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            try:
                return left.translate(table)
            except (TypeError, ValueError, LookupError):
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, table_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            table = await table_t(rt)
            if table is EMPTY or table is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            try:
                return left.translate(table)
            except (TypeError, ValueError, LookupError):
                return INVALID

        return athunk


# =============================================================================
# FORMAT MAP (Binary) - mapping is a value child
# =============================================================================


class FormatMap(ScalarQuery):
    """Format using a mapping: str.format_map(mapping)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, mapping_t = children

        def thunk(rt: Runtime) -> object:
            left = left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            mapping = mapping_t(rt)
            if mapping is EMPTY or mapping is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            try:
                return left.format_map(mapping)
            except (KeyError, IndexError, ValueError, TypeError, AttributeError):
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left_t, mapping_t = children

        async def athunk(rt: Runtime) -> object:
            left = await left_t(rt)
            if left is EMPTY or left is INVALID:
                return INVALID
            mapping = await mapping_t(rt)
            if mapping is EMPTY or mapping is INVALID:
                return INVALID
            if not isinstance(left, str):
                return INVALID
            try:
                return left.format_map(mapping)
            except (KeyError, IndexError, ValueError, TypeError, AttributeError):
                return INVALID

        return athunk
