"""String ops for everybase.

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

from nu.terms import (
    INVALID,
    BinaryCalc,
    NAryCalc,
    Sentinel,
    TernaryCalc,
    UnaryCalc,
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


class UpperOp(UnaryCalc[str]):
    """Convert to uppercase: str.upper()."""

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.upper()


class LowerOp(UnaryCalc[str]):
    """Convert to lowercase: str.lower()."""

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.lower()


class TitleOp(UnaryCalc[str]):
    """Convert to title case: str.title()."""

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.title()


class CapitalizeOp(UnaryCalc[str]):
    """Capitalize first character: str.capitalize()."""

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.capitalize()


class SwapCaseOp(UnaryCalc[str]):
    """Swap case: str.swapcase()."""

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.swapcase()


# =============================================================================
# STRING TESTS (Unary)
# =============================================================================


class IsDigitOp(UnaryCalc[bool]):
    """Check if all digits: str.isdigit()."""

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isdigit()


class IsAlphaOp(UnaryCalc[bool]):
    """Check if all alphabetic: str.isalpha()."""

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isalpha()


class IsAlnumOp(UnaryCalc[bool]):
    """Check if alphanumeric: str.isalnum()."""

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isalnum()


class IsSpaceOp(UnaryCalc[bool]):
    """Check if all whitespace: str.isspace()."""

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isspace()


# =============================================================================
# STRIPPING (Binary)
# =============================================================================


class StripOp(BinaryCalc[str]):
    """Strip whitespace or chars: str.strip(chars)."""

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, str):
            return INVALID
        if right is not None and not isinstance(right, str):
            return INVALID
        return left.strip(right)  # type: ignore


class LStripOp(BinaryCalc[str]):
    """Strip leading whitespace or chars: str.lstrip(chars)."""

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, str):
            return INVALID
        if right is not None and not isinstance(right, str):
            return INVALID
        return left.lstrip(right)  # type: ignore


class RStripOp(BinaryCalc[str]):
    """Strip trailing whitespace or chars: str.rstrip(chars)."""

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


class SplitOp(TernaryCalc[list[str]]):
    """Split string: str.split(sep, maxsplit)."""

    def apply(self, first: object, second: object, third: object) -> list[str] | Sentinel:
        """Apply."""
        if not isinstance(first, str):
            return INVALID
        if second is not None and not isinstance(second, str):
            return INVALID
        return first.split(second, int(third))  # type: ignore


class RSplitOp(TernaryCalc[list[str]]):
    """Right split string: str.rsplit(sep, maxsplit)."""

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


class FindOp(NAryCalc[int]):
    """Find substring: str.find(sub, start, end)."""

    def apply(self, *args: object) -> int | Sentinel:
        """Apply."""
        operand, sub, start, end = args
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        if end is None:
            return operand.find(sub, int(start))  # type: ignore
        return operand.find(sub, int(start), int(end))  # type: ignore


class RFindOp(NAryCalc[int]):
    """Find substring from right: str.rfind(sub, start, end)."""

    def apply(self, *args: object) -> int | Sentinel:
        """Apply."""
        operand, sub, start, end = args
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        if end is None:
            return operand.rfind(sub, int(start))  # type: ignore
        return operand.rfind(sub, int(start), int(end))  # type: ignore


class CountSubstringOp(BinaryCalc[int]):
    """Count substring occurrences: str.count(sub)."""

    def apply(self, left: object, right: object) -> int | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.count(right)


# =============================================================================
# PREFIX/SUFFIX TESTING (Binary)
# =============================================================================


class StartsWithOp(BinaryCalc[bool]):
    """Check if starts with prefix: str.startswith(prefix)."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.startswith(right)


class EndsWithOp(BinaryCalc[bool]):
    """Check if ends with suffix: str.endswith(suffix)."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.endswith(right)


# =============================================================================
# PADDING (Ternary)
# =============================================================================


class CenterOp(TernaryCalc[str]):
    """Center in width: str.center(width, fillchar)."""

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.center(second, fill[0] if fill else " ")


class LJustOp(TernaryCalc[str]):
    """Left justify: str.ljust(width, fillchar)."""

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.ljust(second, fill[0] if fill else " ")


class RJustOp(TernaryCalc[str]):
    """Right justify: str.rjust(width, fillchar)."""

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.rjust(second, fill[0] if fill else " ")


class ZFillOp(BinaryCalc[str]):
    """Zero-fill: str.zfill(width)."""

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, int):
            return INVALID
        return left.zfill(right)


# =============================================================================
# REPLACING
# =============================================================================


class ReplaceOp(NAryCalc[str]):
    """Replace substring: str.replace(old, new, count)."""

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


class EncodeOp(BinaryCalc[bytes]):
    """Encode string to bytes: str.encode(encoding)."""

    def apply(self, left: object, right: object) -> bytes | Sentinel:
        """Apply."""
        if not isinstance(left, str):
            return INVALID
        try:
            return left.encode(str(right) if right else "utf-8")
        except (UnicodeEncodeError, LookupError):
            return INVALID


# =============================================================================
# JOINING (Binary)
# =============================================================================


class JoinOp(BinaryCalc[str]):
    """Join strings: sep.join(seq)."""

    def apply(self, left: object, right: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(right, str):
            return INVALID
        try:
            return right.join(str(x) for x in left)  # type: ignore
        except TypeError:
            return INVALID
