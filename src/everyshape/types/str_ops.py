"""String operations for Term expressions.

This module provides type-safe operations on string Terms:

Case transformation: UpperOp, LowerOp, TitleOp, CapitalizeOp, SwapCaseOp
Stripping: StripOp, LStripOp, RStripOp
Splitting: SplitOp, RSplitOp
Searching: FindOp, RFindOp, CountSubstringOp
Padding: CenterOp, LJustOp, RJustOp, ZFillOp
Testing: StartsWithOp, EndsWithOp, IsDigitOp, IsAlphaOp, IsAlnumOp, IsSpaceOp
Replacing: ReplaceOp
Encoding: EncodeOp

Design principles:
1. Atomic classes: one operation = one class
2. All arguments support Term or literal
3. Proper base class inheritance (UnaryOp, BinaryOp, TernaryOp, NAryOp)
4. Runtime type checking with NAN for invalid types
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.ops.core import BinaryOp, NAryOp, TernaryOp, UnaryOp
from everyshape.typing import NAN, NOT_SET, NotSet, Sentinel, is_notset


if TYPE_CHECKING:
    from everyshape.term import Term

    from .bases import UnionBaseType


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


type OpArgument = Term | UnionBaseType


# =============================================================================
# CASE TRANSFORMATION (Unary)
# =============================================================================


class UpperOp(UnaryOp[str | Sentinel]):
    """Convert to uppercase: str.upper()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.upper()


class LowerOp(UnaryOp[str | Sentinel]):
    """Convert to lowercase: str.lower()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.lower()


class TitleOp(UnaryOp[str | Sentinel]):
    """Convert to title case: str.title()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.title()


class CapitalizeOp(UnaryOp[str | Sentinel]):
    """Capitalize first character: str.capitalize()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.capitalize()


class SwapCaseOp(UnaryOp[str | Sentinel]):
    """Swap case: str.swapcase()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.swapcase()


# =============================================================================
# STRING TESTS (Unary)
# =============================================================================


class IsDigitOp(UnaryOp[bool | Sentinel]):
    """Check if all digits: str.isdigit()."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.isdigit()


class IsAlphaOp(UnaryOp[bool | Sentinel]):
    """Check if all alphabetic: str.isalpha()."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.isalpha()


class IsAlnumOp(UnaryOp[bool | Sentinel]):
    """Check if alphanumeric: str.isalnum()."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.isalnum()


class IsSpaceOp(UnaryOp[bool | Sentinel]):
    """Check if all whitespace: str.isspace()."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.isspace()


# =============================================================================
# STRIPPING (NAryOp - optional chars argument)
# =============================================================================


class StripOp(NAryOp[str | Sentinel]):
    """Strip whitespace or chars: str.strip(chars).

    Args can be Terms for dynamic values.
    """

    def __init__(self, operand: OpArgument, chars: OpArgument | NotSet = NOT_SET) -> None:
        """Initialize strip operation."""
        if is_notset(chars):
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply_op(self, operand: object, chars: object = NOT_SET) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        if is_notset(chars):
            return operand.strip()
        if chars is not None and not isinstance(chars, str):
            return NAN
        return operand.strip(chars)


class LStripOp(NAryOp[str | Sentinel]):
    """Strip leading whitespace or chars: str.lstrip(chars)."""

    def __init__(self, operand: OpArgument, chars: OpArgument | NotSet = NOT_SET) -> None:
        """Initialize lstrip operation."""
        if is_notset(chars):
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply_op(self, operand: object, chars: object = NOT_SET) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        if is_notset(chars):
            return operand.lstrip()
        if chars is not None and not isinstance(chars, str):
            return NAN
        return operand.lstrip(chars)


class RStripOp(NAryOp[str | Sentinel]):
    """Strip trailing whitespace or chars: str.rstrip(chars)."""

    def __init__(self, operand: OpArgument, chars: OpArgument | NotSet = NOT_SET) -> None:
        """Initialize rstrip operation."""
        if is_notset(chars):
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply_op(self, operand: object, chars: object = NOT_SET) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        if is_notset(chars):
            return operand.rstrip()
        if chars is not None and not isinstance(chars, str):
            return NAN
        return operand.rstrip(chars)


# =============================================================================
# SPLITTING (NAryOp - optional sep, maxsplit as Terms)
# =============================================================================


class SplitOp(NAryOp[list[str] | Sentinel]):
    """Split string: str.split(sep, maxsplit).

    All args can be Terms for dynamic values.
    """

    def __init__(
        self,
        operand: OpArgument,
        sep: OpArgument | NotSet = NOT_SET,
        maxsplit: OpArgument = -1,
    ) -> None:
        """Initialize split operation."""
        if is_notset(sep):
            super().__init__(operand, maxsplit)
            self._has_sep = False
        else:
            super().__init__(operand, sep, maxsplit)
            self._has_sep = True

    def _apply_op(self, *args: object) -> list[str] | Sentinel:
        if self._has_sep:
            operand, sep, maxsplit = args
        else:
            operand, maxsplit = args
            sep = None

        if not isinstance(operand, str):
            return NAN
        if sep is not None and not isinstance(sep, str):
            return NAN
        return operand.split(sep, int(maxsplit))  # type: ignore[arg-type]


class RSplitOp(NAryOp[list[str] | Sentinel]):
    """Right split string: str.rsplit(sep, maxsplit)."""

    def __init__(
        self,
        operand: OpArgument,
        sep: OpArgument | NotSet = NOT_SET,
        maxsplit: OpArgument = -1,
    ) -> None:
        """Initialize rsplit operation."""
        if is_notset(sep):
            super().__init__(operand, maxsplit)
            self._has_sep = False
        else:
            super().__init__(operand, sep, maxsplit)
            self._has_sep = True

    def _apply_op(self, *args: object) -> list[str] | Sentinel:
        if self._has_sep:
            operand, sep, maxsplit = args
        else:
            operand, maxsplit = args
            sep = None

        if not isinstance(operand, str):
            return NAN
        if sep is not None and not isinstance(sep, str):
            return NAN
        return operand.rsplit(sep, int(maxsplit))  # type: ignore[arg-type]


# =============================================================================
# SEARCHING (NAryOp for optional start/end, Binary for simple)
# =============================================================================


class FindOp(NAryOp[int | Sentinel]):
    """Find substring: str.find(sub, start, end).

    All args can be Terms.
    """

    def __init__(
        self,
        operand: OpArgument,
        sub: OpArgument,
        start: OpArgument = 0,
        end: OpArgument | NotSet = NOT_SET,
    ) -> None:
        """Initialize find operation."""
        if is_notset(end):
            super().__init__(operand, sub, start)
        else:
            super().__init__(operand, sub, start, end)

    def _apply_op(
        self, operand: object, sub: object, start: object, end: object = NOT_SET
    ) -> int | Sentinel:
        if not isinstance(operand, str) or not isinstance(sub, str):
            return NAN
        if is_notset(end) or end is None:
            return operand.find(sub, int(start))  # type: ignore[arg-type]
        return operand.find(sub, int(start), int(end))  # type: ignore[arg-type]


class RFindOp(NAryOp[int | Sentinel]):
    """Find substring from right: str.rfind(sub, start, end)."""

    def __init__(
        self,
        operand: OpArgument,
        sub: OpArgument,
        start: OpArgument = 0,
        end: OpArgument | NotSet = NOT_SET,
    ) -> None:
        """Initialize rfind operation."""
        if is_notset(end):
            super().__init__(operand, sub, start)
        else:
            super().__init__(operand, sub, start, end)

    def _apply_op(
        self, operand: object, sub: object, start: object, end: object = NOT_SET
    ) -> int | Sentinel:
        if not isinstance(operand, str) or not isinstance(sub, str):
            return NAN
        if is_notset(end) or end is None:
            return operand.rfind(sub, int(start))  # type: ignore[arg-type]
        return operand.rfind(sub, int(start), int(end))  # type: ignore[arg-type]


class CountSubstringOp(BinaryOp[int | Sentinel]):
    """Count substring occurrences: str.count(sub)."""

    def _apply_op(self, operand: object, sub: object) -> int | Sentinel:
        if not isinstance(operand, str) or not isinstance(sub, str):
            return NAN
        return operand.count(sub)


# =============================================================================
# PREFIX/SUFFIX TESTING (Binary)
# =============================================================================


class StartsWithOp(BinaryOp[bool | Sentinel]):
    """Check if starts with prefix: str.startswith(prefix)."""

    def _apply_op(self, operand: object, prefix: object) -> bool | Sentinel:
        if not isinstance(operand, str) or not isinstance(prefix, str):
            return NAN
        return operand.startswith(prefix)


class EndsWithOp(BinaryOp[bool | Sentinel]):
    """Check if ends with suffix: str.endswith(suffix)."""

    def _apply_op(self, operand: object, suffix: object) -> bool | Sentinel:
        if not isinstance(operand, str) or not isinstance(suffix, str):
            return NAN
        return operand.endswith(suffix)


# =============================================================================
# PADDING (TernaryOp - operand, width, fillchar all as Terms)
# =============================================================================


class CenterOp(TernaryOp[str | Sentinel]):
    """Center in width: str.center(width, fillchar)."""

    def _apply_op(self, operand: object, width: object, fillchar: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(width, int):
            return NAN
        fill = str(fillchar) if fillchar else " "
        return operand.center(width, fill[0] if fill else " ")


class LJustOp(TernaryOp[str | Sentinel]):
    """Left justify: str.ljust(width, fillchar)."""

    def _apply_op(self, operand: object, width: object, fillchar: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(width, int):
            return NAN
        fill = str(fillchar) if fillchar else " "
        return operand.ljust(width, fill[0] if fill else " ")


class RJustOp(TernaryOp[str | Sentinel]):
    """Right justify: str.rjust(width, fillchar)."""

    def _apply_op(self, operand: object, width: object, fillchar: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(width, int):
            return NAN
        fill = str(fillchar) if fillchar else " "
        return operand.rjust(width, fill[0] if fill else " ")


class ZFillOp(BinaryOp[str | Sentinel]):
    """Zero-fill: str.zfill(width)."""

    def _apply_op(self, operand: object, width: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(width, int):
            return NAN
        return operand.zfill(width)


# =============================================================================
# REPLACING (NAryOp - operand, old, new, count all as Terms)
# =============================================================================


class ReplaceOp(NAryOp[str | Sentinel]):
    """Replace substring: str.replace(old, new, count).

    All args can be Terms.
    """

    def __init__(
        self,
        operand: OpArgument,
        old: OpArgument,
        new: OpArgument,
        count: OpArgument = -1,
    ) -> None:
        """Initialize replace operation."""
        super().__init__(operand, old, new, count)

    def _apply_op(self, operand: object, old: object, new: object, count: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(old, str) or not isinstance(new, str):
            return NAN
        count_int = int(count)  # type: ignore[arg-type]
        if count_int == -1:
            return operand.replace(old, new)
        return operand.replace(old, new, count_int)


# =============================================================================
# ENCODING (Binary - operand, encoding as Terms)
# =============================================================================


class EncodeOp(BinaryOp[bytes | Sentinel]):
    """Encode string to bytes: str.encode(encoding)."""

    def _apply_op(self, operand: object, encoding: object) -> bytes | Sentinel:
        if not isinstance(operand, str):
            return NAN
        try:
            return operand.encode(str(encoding) if encoding else "utf-8")
        except (UnicodeEncodeError, LookupError):
            return NAN
