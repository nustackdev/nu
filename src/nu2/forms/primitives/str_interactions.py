"""String-specific interactions.

All str methods are pure (str is immutable), so every interaction is a Query.

Case transformation: UpperQuery, LowerQuery, TitleQuery, CapitalizeQuery, SwapCaseQuery, CasefoldQuery
Stripping: StripQuery, LStripQuery, RStripQuery
Splitting: SplitQuery, RSplitQuery, SplitLinesQuery, PartitionQuery, RPartitionQuery
Searching: FindQuery, RFindQuery, IndexQuery, RIndexQuery, CountSubstringQuery
Padding: CenterQuery, LJustQuery, RJustQuery, ZFillQuery, ExpandTabsQuery
Testing: StartsWithQuery, EndsWithQuery, IsDigitQuery, IsAlphaQuery, IsAlnumQuery, IsSpaceQuery,
    IsNumericQuery, IsDecimalQuery, IsIdentifierQuery, IsPrintableQuery, IsTitleQuery, IsUpperQuery,
    IsLowerQuery, IsAsciiQuery
Replacing: ReplaceQuery, RemovePrefixQuery, RemoveSuffixQuery, TranslateQuery
Formatting: FormatMapQuery
Encoding: EncodeQuery
Joining: JoinQuery
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "CapitalizeQuery",
    "CasefoldQuery",
    "CenterQuery",
    "CountSubstringQuery",
    "EncodeQuery",
    "EndsWithQuery",
    "ExpandTabsQuery",
    "FindQuery",
    "FormatMapQuery",
    "IndexQuery",
    "IsAlnumQuery",
    "IsAlphaQuery",
    "IsAsciiQuery",
    "IsDecimalQuery",
    "IsDigitQuery",
    "IsIdentifierQuery",
    "IsLowerQuery",
    "IsNumericQuery",
    "IsPrintableQuery",
    "IsSpaceQuery",
    "IsTitleQuery",
    "IsUpperQuery",
    "JoinQuery",
    "LJustQuery",
    "LStripQuery",
    "LowerQuery",
    "PartitionQuery",
    "RFindQuery",
    "RIndexQuery",
    "RJustQuery",
    "RPartitionQuery",
    "RSplitQuery",
    "RStripQuery",
    "RemovePrefixQuery",
    "RemoveSuffixQuery",
    "ReplaceQuery",
    "SplitLinesQuery",
    "SplitQuery",
    "StartsWithQuery",
    "StripQuery",
    "SwapCaseQuery",
    "TitleQuery",
    "TranslateQuery",
    "UpperQuery",
    "ZFillQuery",
]


# =============================================================================
# CASE TRANSFORMATION (Unary)
# =============================================================================


class UpperQuery(ScalarQuery):
    """Convert to uppercase: str.upper()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.upper()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.upper()

        return athunk


class LowerQuery(ScalarQuery):
    """Convert to lowercase: str.lower()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.lower()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.lower()

        return athunk


class TitleQuery(ScalarQuery):
    """Convert to title case: str.title()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.title()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.title()

        return athunk


class CapitalizeQuery(ScalarQuery):
    """Capitalize first character: str.capitalize()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.capitalize()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.capitalize()

        return athunk


class SwapCaseQuery(ScalarQuery):
    """Swap case: str.swapcase()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.swapcase()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class IsDigitQuery(ScalarQuery):
    """Check if all digits: str.isdigit()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isdigit()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isdigit()

        return athunk


class IsAlphaQuery(ScalarQuery):
    """Check if all alphabetic: str.isalpha()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isalpha()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isalpha()

        return athunk


class IsAlnumQuery(ScalarQuery):
    """Check if alphanumeric: str.isalnum()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isalnum()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isalnum()

        return athunk


class IsSpaceQuery(ScalarQuery):
    """Check if all whitespace: str.isspace()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isspace()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class StripQuery(ScalarQuery):
    """Strip whitespace or chars: str.strip(chars)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class LStripQuery(ScalarQuery):
    """Strip leading whitespace or chars: str.lstrip(chars)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RStripQuery(ScalarQuery):
    """Strip trailing whitespace or chars: str.rstrip(chars)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SplitQuery(ScalarQuery):
    """Split string: str.split(sep, maxsplit)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RSplitQuery(ScalarQuery):
    """Right split string: str.rsplit(sep, maxsplit)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class FindQuery(ScalarQuery):
    """Find substring: str.find(sub, start, end)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RFindQuery(ScalarQuery):
    """Find substring from right: str.rfind(sub, start, end)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class CountSubstringQuery(ScalarQuery):
    """Count substring occurrences: str.count(sub)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class StartsWithQuery(ScalarQuery):
    """Check if starts with prefix: str.startswith(prefix)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class EndsWithQuery(ScalarQuery):
    """Check if ends with suffix: str.endswith(suffix)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class CenterQuery(ScalarQuery):
    """Center in width: str.center(width, fillchar)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class LJustQuery(ScalarQuery):
    """Left justify: str.ljust(width, fillchar)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RJustQuery(ScalarQuery):
    """Right justify: str.rjust(width, fillchar)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class ZFillQuery(ScalarQuery):
    """Zero-fill: str.zfill(width)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class ReplaceQuery(ScalarQuery):
    """Replace substring: str.replace(old, new, count)."""

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


class EncodeQuery(ScalarQuery):
    """Encode string to bytes: str.encode(encoding)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class JoinQuery(ScalarQuery):
    """Join iterable elements into string: sep.join(seq)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class CasefoldQuery(ScalarQuery):
    """Casefold for caseless matching: str.casefold()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.casefold()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class IsNumericQuery(ScalarQuery):
    """Check if all numeric: str.isnumeric()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isnumeric()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isnumeric()

        return athunk


class IsDecimalQuery(ScalarQuery):
    """Check if all decimal: str.isdecimal()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isdecimal()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isdecimal()

        return athunk


class IsIdentifierQuery(ScalarQuery):
    """Check if valid identifier: str.isidentifier()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isidentifier()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isidentifier()

        return athunk


class IsPrintableQuery(ScalarQuery):
    """Check if all printable: str.isprintable()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isprintable()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isprintable()

        return athunk


class IsTitleQuery(ScalarQuery):
    """Check if titlecased: str.istitle()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.istitle()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.istitle()

        return athunk


class IsUpperQuery(ScalarQuery):
    """Check if all cased chars uppercase: str.isupper()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isupper()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isupper()

        return athunk


class IsLowerQuery(ScalarQuery):
    """Check if all cased chars lowercase: str.islower()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.islower()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            v = await operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.islower()

        return athunk


class IsAsciiQuery(ScalarQuery):
    """Check if all ASCII (empty is True): str.isascii()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            v = operand(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            if not isinstance(v, str):
                return INVALID
            return v.isascii()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class ExpandTabsQuery(ScalarQuery):
    """Expand tabs to spaces: str.expandtabs(tabsize)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class PartitionQuery(ScalarQuery):
    """Split around first occurrence of sep: str.partition(sep)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RPartitionQuery(ScalarQuery):
    """Split around last occurrence of sep: str.rpartition(sep)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SplitLinesQuery(ScalarQuery):
    """Split at line boundaries: str.splitlines(keepends)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class IndexQuery(ScalarQuery):
    """Find substring index, error if absent: str.index(sub, start, end)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RIndexQuery(ScalarQuery):
    """Find substring index from right, error if absent: str.rindex(sub, start, end)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RemovePrefixQuery(ScalarQuery):
    """Remove prefix if present: str.removeprefix(prefix)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RemoveSuffixQuery(ScalarQuery):
    """Remove suffix if present: str.removesuffix(suffix)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class TranslateQuery(ScalarQuery):
    """MapQuery characters through a table: str.translate(table)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class FormatMapQuery(ScalarQuery):
    """Format using a mapping: str.format_map(mapping)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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
