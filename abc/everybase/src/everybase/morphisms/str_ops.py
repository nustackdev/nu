"""String morphisms for everybase.

Case transformation: UpperOp, LowerOp, TitleOp, CapitalizeOp, SwapCaseOp
Stripping: StripOp, LStripOp, RStripOp
Splitting: SplitOp, RSplitOp
Searching: FindOp, RFindOp, CountSubstringOp
Padding: CenterOp, LJustOp, RJustOp, ZFillOp
Testing: StartsWithOp, EndsWithOp, IsDigitOp, IsAlphaOp, IsAlnumOp, IsSpaceOp
Replacing: ReplaceOp
Encoding: EncodeOp
"""

from __future__ import annotations

from every import (
    INVALID,
    BinaryMorphism,
    NAryMorphism,
    Operation,
    Sentinel,
    TernaryMorphism,
    UnaryMorphism,
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


class UpperOp(Operation, UnaryMorphism[str | Sentinel]):
    """Convert to uppercase: str.upper()."""

    def _apply(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.upper()


class LowerOp(Operation, UnaryMorphism[str | Sentinel]):
    """Convert to lowercase: str.lower()."""

    def _apply(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.lower()


class TitleOp(Operation, UnaryMorphism[str | Sentinel]):
    """Convert to title case: str.title()."""

    def _apply(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.title()


class CapitalizeOp(Operation, UnaryMorphism[str | Sentinel]):
    """Capitalize first character: str.capitalize()."""

    def _apply(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.capitalize()


class SwapCaseOp(Operation, UnaryMorphism[str | Sentinel]):
    """Swap case: str.swapcase()."""

    def _apply(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.swapcase()


# =============================================================================
# STRING TESTS (Unary)
# =============================================================================


class IsDigitOp(Operation, UnaryMorphism[bool | Sentinel]):
    """Check if all digits: str.isdigit()."""

    def _apply(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.isdigit()


class IsAlphaOp(Operation, UnaryMorphism[bool | Sentinel]):
    """Check if all alphabetic: str.isalpha()."""

    def _apply(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.isalpha()


class IsAlnumOp(Operation, UnaryMorphism[bool | Sentinel]):
    """Check if alphanumeric: str.isalnum()."""

    def _apply(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.isalnum()


class IsSpaceOp(Operation, UnaryMorphism[bool | Sentinel]):
    """Check if all whitespace: str.isspace()."""

    def _apply(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        return operand.isspace()


# =============================================================================
# STRIPPING (NAryMorphism - optional chars argument)
# =============================================================================


class StripOp(Operation, NAryMorphism[str | Sentinel]):
    """Strip whitespace or chars: str.strip(chars)."""

    def __init__(self, operand: object, chars: object | None = None) -> None:
        """Initialize strip operation."""
        if chars is None:
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply(self, *args: object) -> str | Sentinel:
        if len(args) == 1:
            operand = args[0]
            chars = None
        else:
            operand, chars = args
        if not isinstance(operand, str):
            return INVALID
        if chars is not None and not isinstance(chars, str):
            return INVALID
        return operand.strip(chars)  # type: ignore


class LStripOp(Operation, NAryMorphism[str | Sentinel]):
    """Strip leading whitespace or chars: str.lstrip(chars)."""

    def __init__(self, operand: object, chars: object | None = None) -> None:
        """Initialize lstrip operation."""
        if chars is None:
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply(self, *args: object) -> str | Sentinel:
        if len(args) == 1:
            operand = args[0]
            chars = None
        else:
            operand, chars = args
        if not isinstance(operand, str):
            return INVALID
        if chars is not None and not isinstance(chars, str):
            return INVALID
        return operand.lstrip(chars)  # type: ignore


class RStripOp(Operation, NAryMorphism[str | Sentinel]):
    """Strip trailing whitespace or chars: str.rstrip(chars)."""

    def __init__(self, operand: object, chars: object | None = None) -> None:
        """Initialize rstrip operation."""
        if chars is None:
            super().__init__(operand)
        else:
            super().__init__(operand, chars)

    def _apply(self, *args: object) -> str | Sentinel:
        if len(args) == 1:
            operand = args[0]
            chars = None
        else:
            operand, chars = args
        if not isinstance(operand, str):
            return INVALID
        if chars is not None and not isinstance(chars, str):
            return INVALID
        return operand.rstrip(chars)  # type: ignore


# =============================================================================
# SPLITTING (NAryMorphism)
# =============================================================================


class SplitOp(Operation, NAryMorphism[list[str] | Sentinel]):
    """Split string: str.split(sep, maxsplit)."""

    def __init__(
        self,
        operand: object,
        sep: object | None = None,
        maxsplit: object = -1,
    ) -> None:
        """Initialize split operation."""
        if sep is None:
            super().__init__(operand, maxsplit)
            self._has_sep = False
        else:
            super().__init__(operand, sep, maxsplit)
            self._has_sep = True

    def _apply(self, *args: object) -> list[str] | Sentinel:
        if self._has_sep:
            operand, sep, maxsplit = args
        else:
            operand, maxsplit = args
            sep = None
        if not isinstance(operand, str):
            return INVALID
        if sep is not None and not isinstance(sep, str):
            return INVALID
        return operand.split(sep, int(maxsplit))  # type: ignore


class RSplitOp(Operation, NAryMorphism[list[str] | Sentinel]):
    """Right split string: str.rsplit(sep, maxsplit)."""

    def __init__(
        self,
        operand: object,
        sep: object | None = None,
        maxsplit: object = -1,
    ) -> None:
        """Initialize rsplit operation."""
        if sep is None:
            super().__init__(operand, maxsplit)
            self._has_sep = False
        else:
            super().__init__(operand, sep, maxsplit)
            self._has_sep = True

    def _apply(self, *args: object) -> list[str] | Sentinel:
        if self._has_sep:
            operand, sep, maxsplit = args
        else:
            operand, maxsplit = args
            sep = None
        if not isinstance(operand, str):
            return INVALID
        if sep is not None and not isinstance(sep, str):
            return INVALID
        return operand.rsplit(sep, int(maxsplit))  # type: ignore


# =============================================================================
# SEARCHING (NAryMorphism/BinaryMorphism)
# =============================================================================


class FindOp(Operation, NAryMorphism[int | Sentinel]):
    """Find substring: str.find(sub, start, end)."""

    def __init__(
        self,
        operand: object,
        sub: object,
        start: object = 0,
        end: object | None = None,
    ) -> None:
        """Initialize find operation."""
        if end is None:
            super().__init__(operand, sub, start)
        else:
            super().__init__(operand, sub, start, end)

    def _apply(self, *args: object) -> int | Sentinel:
        if len(args) == 3:
            operand, sub, start = args
            end = None
        else:
            operand, sub, start, end = args
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        if end is None:
            return operand.find(sub, int(start))  # type: ignore
        return operand.find(sub, int(start), int(end))  # type: ignore


class RFindOp(Operation, NAryMorphism[int | Sentinel]):
    """Find substring from right: str.rfind(sub, start, end)."""

    def __init__(
        self,
        operand: object,
        sub: object,
        start: object = 0,
        end: object | None = None,
    ) -> None:
        """Initialize rfind operation."""
        if end is None:
            super().__init__(operand, sub, start)
        else:
            super().__init__(operand, sub, start, end)

    def _apply(self, *args: object) -> int | Sentinel:
        if len(args) == 3:
            operand, sub, start = args
            end = None
        else:
            operand, sub, start, end = args
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        if end is None:
            return operand.rfind(sub, int(start))  # type: ignore
        return operand.rfind(sub, int(start), int(end))  # type: ignore


class CountSubstringOp(Operation, BinaryMorphism[int | Sentinel]):
    """Count substring occurrences: str.count(sub)."""

    def _apply(self, operand: object, sub: object) -> int | Sentinel:
        if not isinstance(operand, str) or not isinstance(sub, str):
            return INVALID
        return operand.count(sub)


# =============================================================================
# PREFIX/SUFFIX TESTING (Binary)
# =============================================================================


class StartsWithOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Check if starts with prefix: str.startswith(prefix)."""

    def _apply(self, operand: object, prefix: object) -> bool | Sentinel:
        if not isinstance(operand, str) or not isinstance(prefix, str):
            return INVALID
        return operand.startswith(prefix)


class EndsWithOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Check if ends with suffix: str.endswith(suffix)."""

    def _apply(self, operand: object, suffix: object) -> bool | Sentinel:
        if not isinstance(operand, str) or not isinstance(suffix, str):
            return INVALID
        return operand.endswith(suffix)


# =============================================================================
# PADDING (TernaryMorphism)
# =============================================================================


class CenterOp(Operation, TernaryMorphism[str | Sentinel]):
    """Center in width: str.center(width, fillchar)."""

    def _apply(self, operand: object, width: object, fillchar: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(width, int):
            return INVALID
        fill = str(fillchar) if fillchar else " "
        return operand.center(width, fill[0] if fill else " ")


class LJustOp(Operation, TernaryMorphism[str | Sentinel]):
    """Left justify: str.ljust(width, fillchar)."""

    def _apply(self, operand: object, width: object, fillchar: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(width, int):
            return INVALID
        fill = str(fillchar) if fillchar else " "
        return operand.ljust(width, fill[0] if fill else " ")


class RJustOp(Operation, TernaryMorphism[str | Sentinel]):
    """Right justify: str.rjust(width, fillchar)."""

    def _apply(self, operand: object, width: object, fillchar: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(width, int):
            return INVALID
        fill = str(fillchar) if fillchar else " "
        return operand.rjust(width, fill[0] if fill else " ")


class ZFillOp(Operation, BinaryMorphism[str | Sentinel]):
    """Zero-fill: str.zfill(width)."""

    def _apply(self, operand: object, width: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(width, int):
            return INVALID
        return operand.zfill(width)


# =============================================================================
# REPLACING (NAryMorphism)
# =============================================================================


class ReplaceOp(Operation, NAryMorphism[str | Sentinel]):
    """Replace substring: str.replace(old, new, count)."""

    def __init__(
        self,
        operand: object,
        old: object,
        new: object,
        count: object = -1,
    ) -> None:
        """Initialize replace operation."""
        super().__init__(operand, old, new, count)

    def _apply(self, operand: object, old: object, new: object, count: object) -> str | Sentinel:
        if not isinstance(operand, str) or not isinstance(old, str) or not isinstance(new, str):
            return INVALID
        count_int = int(count)  # type: ignore
        if count_int == -1:
            return operand.replace(old, new)
        return operand.replace(old, new, count_int)


# =============================================================================
# ENCODING (Binary)
# =============================================================================


class EncodeOp(Operation, BinaryMorphism[bytes | Sentinel]):
    """Encode string to bytes: str.encode(encoding)."""

    def _apply(self, operand: object, encoding: object) -> bytes | Sentinel:
        if not isinstance(operand, str):
            return INVALID
        try:
            return operand.encode(str(encoding) if encoding else "utf-8")
        except (UnicodeEncodeError, LookupError):
            return INVALID
