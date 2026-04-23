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


# =============================================================================
# CASE TRANSFORMATION (Unary)
# =============================================================================


class UpperOp(UnaryQuery[str]):
    """Convert to uppercase: str.upper()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.upper()


class LowerOp(UnaryQuery[str]):
    """Convert to lowercase: str.lower()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.lower()


class TitleOp(UnaryQuery[str]):
    """Convert to title case: str.title()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.title()


class CapitalizeOp(UnaryQuery[str]):
    """Capitalize first character: str.capitalize()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.capitalize()


class SwapCaseOp(UnaryQuery[str]):
    """Swap case: str.swapcase()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.swapcase()


# =============================================================================
# STRING TESTS (Unary)
# =============================================================================


class IsDigitOp(UnaryQuery[bool]):
    """Check if all digits: str.isdigit()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isdigit()


class IsAlphaOp(UnaryQuery[bool]):
    """Check if all alphabetic: str.isalpha()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isalpha()


class IsAlnumOp(UnaryQuery[bool]):
    """Check if alphanumeric: str.isalnum()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isalnum()


class IsSpaceOp(UnaryQuery[bool]):
    """Check if all whitespace: str.isspace()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isspace()


# =============================================================================
# STRIPPING (Binary)
# =============================================================================


class StripOp(BinaryQuery[str]):
    """Strip whitespace or chars: str.strip(chars)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, str):
            return INVALID
        if right is not None and not isinstance(right, str):
            return INVALID
        return left.strip(right)  # type: ignore


class LStripOp(BinaryQuery[str]):
    """Strip leading whitespace or chars: str.lstrip(chars)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, str):
            return INVALID
        if right is not None and not isinstance(right, str):
            return INVALID
        return left.lstrip(right)  # type: ignore


class RStripOp(BinaryQuery[str]):
    """Strip trailing whitespace or chars: str.rstrip(chars)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, str):
            return INVALID
        if right is not None and not isinstance(right, str):
            return INVALID
        return left.rstrip(right)  # type: ignore


# =============================================================================
# SPLITTING (Ternary)
# =============================================================================


class SplitOp(TernaryQuery[list[str]]):
    """Split string: str.split(sep, maxsplit)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> list[str] | Sentinel:
        """Apply."""
        if not isinstance(first, str):
            return INVALID
        if second is not None and not isinstance(second, str):
            return INVALID
        return first.split(second, int(third))  # type: ignore


class RSplitOp(TernaryQuery[list[str]]):
    """Right split string: str.rsplit(sep, maxsplit)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> list[str] | Sentinel:
        """Apply."""
        if not isinstance(first, str):
            return INVALID
        if second is not None and not isinstance(second, str):
            return INVALID
        return first.rsplit(second, int(third))  # type: ignore


# =============================================================================
# SEARCHING
# =============================================================================


class FindOp(ScalarQuery[int]):
    """Find substring: str.find(sub, start, end)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, *args: object) -> int | Sentinel:
        """Apply."""
        operand, sub, start, end = args
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        if end is None:
            return operand.find(sub, int(start))  # type: ignore
        return operand.find(sub, int(start), int(end))  # type: ignore


class RFindOp(ScalarQuery[int]):
    """Find substring from right: str.rfind(sub, start, end)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, *args: object) -> int | Sentinel:
        """Apply."""
        operand, sub, start, end = args
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        if end is None:
            return operand.rfind(sub, int(start))  # type: ignore
        return operand.rfind(sub, int(start), int(end))  # type: ignore


class CountSubstringOp(BinaryQuery[int]):
    """Count substring occurrences: str.count(sub)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.count(right)


# =============================================================================
# PREFIX/SUFFIX TESTING (Binary)
# =============================================================================


class StartsWithOp(BinaryQuery[bool]):
    """Check if starts with prefix: str.startswith(prefix)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.startswith(right)


class EndsWithOp(BinaryQuery[bool]):
    """Check if ends with suffix: str.endswith(suffix)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.endswith(right)


# =============================================================================
# PADDING (Ternary)
# =============================================================================


class CenterOp(TernaryQuery[str]):
    """Center in width: str.center(width, fillchar)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.center(second, fill[0] if fill else " ")


class LJustOp(TernaryQuery[str]):
    """Left justify: str.ljust(width, fillchar)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.ljust(second, fill[0] if fill else " ")


class RJustOp(TernaryQuery[str]):
    """Right justify: str.rjust(width, fillchar)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.rjust(second, fill[0] if fill else " ")


class ZFillOp(BinaryQuery[str]):
    """Zero-fill: str.zfill(width)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, int):
            return INVALID
        return left.zfill(right)


# =============================================================================
# REPLACING
# =============================================================================


class ReplaceOp(ScalarQuery[str]):
    """Replace substring: str.replace(old, new, count)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, *args: object) -> str | Sentinel:
        """Apply."""
        operand, old, new, count = args
        if not isinstance(operand, str) or not isinstance(old, str) or not isinstance(new, str):
            return INVALID
        count_int = int(count)  # type: ignore
        if count_int == -1:
            return operand.replace(old, new)
        return operand.replace(old, new, count_int)


# =============================================================================
# ENCODING (Binary)
# =============================================================================


class EncodeOp(BinaryQuery[bytes]):
    """Encode string to bytes: str.encode(encoding)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(left, str):
            return INVALID
        try:
            return left.encode(str(right) if right else "utf-8")
        except (UnicodeEncodeError, LookupError):
            return INVALID


# =============================================================================
# JOINING
# =============================================================================


class JoinOp(BinaryQuery[str]):
    """Join iterable elements into string: sep.join(seq)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, str):
            return INVALID
        try:
            return left.join(str(x) for x in right)  # type: ignore
        except TypeError:
            return INVALID
