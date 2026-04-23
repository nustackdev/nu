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
    BinaryScalar,
    Mode,
    NAryScalar,
    Sentinel,
    TernaryScalar,
    UnaryScalar,
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


class UpperOp(UnaryScalar[str]):
    """Convert to uppercase: str.upper()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.upper()


class LowerOp(UnaryScalar[str]):
    """Convert to lowercase: str.lower()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.lower()


class TitleOp(UnaryScalar[str]):
    """Convert to title case: str.title()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.title()


class CapitalizeOp(UnaryScalar[str]):
    """Capitalize first character: str.capitalize()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.capitalize()


class SwapCaseOp(UnaryScalar[str]):
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


class IsDigitOp(UnaryScalar[bool]):
    """Check if all digits: str.isdigit()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isdigit()


class IsAlphaOp(UnaryScalar[bool]):
    """Check if all alphabetic: str.isalpha()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isalpha()


class IsAlnumOp(UnaryScalar[bool]):
    """Check if alphanumeric: str.isalnum()."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(operand, str):
            return INVALID
        return operand.isalnum()


class IsSpaceOp(UnaryScalar[bool]):
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


class StripOp(BinaryScalar[str]):
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


class LStripOp(BinaryScalar[str]):
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


class RStripOp(BinaryScalar[str]):
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


class SplitOp(TernaryScalar[list[str]]):
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


class RSplitOp(TernaryScalar[list[str]]):
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


class FindOp(NAryScalar[int]):
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


class RFindOp(NAryScalar[int]):
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


class CountSubstringOp(BinaryScalar[int]):
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


class StartsWithOp(BinaryScalar[bool]):
    """Check if starts with prefix: str.startswith(prefix)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, str) or not isinstance(right, str):
            return INVALID
        return left.startswith(right)


class EndsWithOp(BinaryScalar[bool]):
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


class CenterOp(TernaryScalar[str]):
    """Center in width: str.center(width, fillchar)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.center(second, fill[0] if fill else " ")


class LJustOp(TernaryScalar[str]):
    """Left justify: str.ljust(width, fillchar)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.ljust(second, fill[0] if fill else " ")


class RJustOp(TernaryScalar[str]):
    """Right justify: str.rjust(width, fillchar)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> str | Sentinel:
        """Apply."""
        if not isinstance(first, str) or not isinstance(second, int):
            return INVALID
        fill = str(third) if third else " "
        return first.rjust(second, fill[0] if fill else " ")


class ZFillOp(BinaryScalar[str]):
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


class ReplaceOp(NAryScalar[str]):
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


class EncodeOp(BinaryScalar[bytes]):
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


class JoinOp(BinaryScalar[str]):
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
