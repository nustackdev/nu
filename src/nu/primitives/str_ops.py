"""String-specific ops.

Case transformation: UpperOp, LowerOp, TitleOp, CapitalizeOp, SwapCaseOp
Stripping: StripOp, LStripOp, RStripOp
Splitting: SplitOp, RSplitOp
Searching: FindOp, RFindOp, CountSubstringOp
Padding: CenterOp, LJustOp, RJustOp, ZFillOp
Testing: StartsWithOp, EndsWithOp, IsDigitOp, IsAlphaOp, IsAlnumOp, IsSpaceOp
Replacing: ReplaceOp
Encoding: EncodeOp
Joining: JoinOp
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


__all__ = [
    "CapitalizeOp",
    "CenterOp",
    "CountSubstringOp",
    "EncodeOp",
    "EndsWithOp",
    "FindOp",
    "IsAlnumOp",
    "IsAlphaOp",
    "IsDigitOp",
    "IsSpaceOp",
    "JoinOp",
    "LJustOp",
    "LStripOp",
    "LowerOp",
    "RFindOp",
    "RJustOp",
    "RSplitOp",
    "RStripOp",
    "ReplaceOp",
    "SplitOp",
    "StartsWithOp",
    "StripOp",
    "SwapCaseOp",
    "TitleOp",
    "UpperOp",
    "ZFillOp",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# CASE TRANSFORMATION (Unary)
# =============================================================================


class UpperOp(ScalarQuery):
    """Convert to uppercase: str.upper()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.upper()


class LowerOp(ScalarQuery):
    """Convert to lowercase: str.lower()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.lower()


class TitleOp(ScalarQuery):
    """Convert to title case: str.title()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.title()


class CapitalizeOp(ScalarQuery):
    """Capitalize first character: str.capitalize()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.capitalize()


class SwapCaseOp(ScalarQuery):
    """Swap case: str.swapcase()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.swapcase()


# =============================================================================
# STRING TESTS (Unary)
# =============================================================================


class IsDigitOp(ScalarQuery):
    """Check if all digits: str.isdigit()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.isdigit()


class IsAlphaOp(ScalarQuery):
    """Check if all alphabetic: str.isalpha()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.isalpha()


class IsAlnumOp(ScalarQuery):
    """Check if alphanumeric: str.isalnum()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.isalnum()


class IsSpaceOp(ScalarQuery):
    """Check if all whitespace: str.isspace()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, str):
            return INVALID
        return operand.isspace()


# =============================================================================
# STRIPPING (Binary)
# =============================================================================


class StripOp(ScalarQuery):
    """Strip whitespace or chars: str.strip(chars)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str):
            return INVALID
        if right is not None and not isinstance(right, str):
            return INVALID
        return left.strip(right)


class LStripOp(ScalarQuery):
    """Strip leading whitespace or chars: str.lstrip(chars)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str):
            return INVALID
        if right is not None and not isinstance(right, str):
            return INVALID
        return left.lstrip(right)


class RStripOp(ScalarQuery):
    """Strip trailing whitespace or chars: str.rstrip(chars)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str):
            return INVALID
        if right is not None and not isinstance(right, str):
            return INVALID
        return left.rstrip(right)


# =============================================================================
# SPLITTING (Ternary)
# =============================================================================


class SplitOp(ScalarQuery):
    """Split string: str.split(sep, maxsplit)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        first, second, third = ops
        if not isinstance(first, str):
            return INVALID
        if second is not None and not isinstance(second, str):
            return INVALID
        return first.split(second, int(third))


class RSplitOp(ScalarQuery):
    """Right split string: str.rsplit(sep, maxsplit)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        first, second, third = ops
        if not isinstance(first, str):
            return INVALID
        if second is not None and not isinstance(second, str):
            return INVALID
        return first.rsplit(second, int(third))


# =============================================================================
# SEARCHING
# =============================================================================


class FindOp(ScalarQuery):
    """Find substring: str.find(sub, start, end)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any, d: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c, d)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand, sub, start, end = ops
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        if end is None:
            return operand.find(sub, int(start))
        return operand.find(sub, int(start), int(end))


class RFindOp(ScalarQuery):
    """Find substring from right: str.rfind(sub, start, end)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any, d: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c, d)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand, sub, start, end = ops
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        if end is None:
            return operand.rfind(sub, int(start))
        return operand.rfind(sub, int(start), int(end))


class CountSubstringOp(ScalarQuery):
    """Count substring occurrences: str.count(sub)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.count(right)


# =============================================================================
# PREFIX/SUFFIX TESTING (Binary)
# =============================================================================


class StartsWithOp(ScalarQuery):
    """Check if starts with prefix: str.startswith(prefix)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.startswith(right)


class EndsWithOp(ScalarQuery):
    """Check if ends with suffix: str.endswith(suffix)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.endswith(right)


# =============================================================================
# PADDING (Ternary)
# =============================================================================


class CenterOp(ScalarQuery):
    """Center in width: str.center(width, fillchar)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        first, second, third = ops
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.center(second, fill[0] if fill else " ")


class LJustOp(ScalarQuery):
    """Left justify: str.ljust(width, fillchar)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        first, second, third = ops
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.ljust(second, fill[0] if fill else " ")


class RJustOp(ScalarQuery):
    """Right justify: str.rjust(width, fillchar)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        first, second, third = ops
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.rjust(second, fill[0] if fill else " ")


class ZFillOp(ScalarQuery):
    """Zero-fill: str.zfill(width)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str) or not isinstance(right, int):
            return INVALID
        return left.zfill(right)


# =============================================================================
# REPLACING
# =============================================================================


class ReplaceOp(ScalarQuery):
    """Replace substring: str.replace(old, new, count)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, a: Any, b: Any, c: Any, d: Any) -> None:  # noqa: ANN401
        super().__init__(a, b, c, d)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand, old, new, count = ops
        if not isinstance(operand, str) or not isinstance(old, str) or not isinstance(new, str):
            return INVALID
        count_int = int(count)
        if count_int == -1:
            return operand.replace(old, new)
        return operand.replace(old, new, count_int)


# =============================================================================
# ENCODING (Binary)
# =============================================================================


class EncodeOp(ScalarQuery):
    """Encode string to bytes: str.encode(encoding)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str):
            return INVALID
        try:
            return left.encode(str(right) if right else "utf-8")
        except (UnicodeEncodeError, LookupError):
            return INVALID


# =============================================================================
# JOINING
# =============================================================================


class JoinOp(ScalarQuery):
    """Join iterable elements into string: sep.join(seq)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        left, right = ops
        if not isinstance(left, str):
            return INVALID
        try:
            return left.join(str(x) for x in right)
        except TypeError:
            return INVALID
