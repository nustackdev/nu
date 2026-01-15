"""String types for Term expressions.

This module provides StrType including all string-specific methods.
StringMethodsBase is merged directly into StrType.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.term.conversion import literal

from ..bases import (
    AddableBase,
    ComparisonBase,
    ContainableBase,
    LengthableBase,
    LogicalBase,
    SliceableBase,
    Type,
)


if TYPE_CHECKING:
    from everyshape.term.term import Term

    from ..bool.type import BoolType
    from ..bytes.type import BytesType
    from ..int.type import IntType
    from ..list.type import ListType


__all__ = [
    "StrType",
]


class StrType(
    AddableBase[str, "StrType"],
    LengthableBase,
    SliceableBase["StrType"],
    ContainableBase[str],
    ComparisonBase["str | StrType"],
    LogicalBase["str | StrType", "BoolType"],
    Type[str],
):
    """String type - represents str expressions (literal or computed).

    Supports concatenation, string operations, comparison, and logical operations.

    Example:
        >>> x = StrType("hello")
        >>> y = x + " world"  # Returns StrType
        >>> z = x.upper()  # Returns StrType
    """

    def _wrap_logical_result(self, operand: Term) -> Term:
        from ..bool.type import BoolType

        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from ..bool.type import BoolType

        return BoolType(operand)

    def _wrap_string_result(self, operand: Term) -> Term:
        return StrType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        return StrType(operand)

    def __add__(self, other: str | StrType) -> StrType:
        from everyshape.ops import AddOp

        return StrType(AddOp(self, literal(other)))

    def __radd__(self, other: str) -> StrType:
        from everyshape.ops import AddOp

        return StrType(AddOp(literal(other), self))

    # =========================================================================
    # STRING-SPECIFIC METHODS (merged from StringMethodsBase)
    # =========================================================================

    # Case transformation
    def upper(self) -> StrType:
        """Convert to uppercase."""
        from everyshape.types.str.ops import UpperOp

        return cast("StrType", self._wrap_string_result(UpperOp(self)))

    def lower(self) -> StrType:
        """Convert to lowercase."""
        from everyshape.types.str.ops import LowerOp

        return cast("StrType", self._wrap_string_result(LowerOp(self)))

    def title(self) -> StrType:
        """Convert to title case."""
        from everyshape.types.str.ops import TitleOp

        return cast("StrType", self._wrap_string_result(TitleOp(self)))

    def capitalize(self) -> StrType:
        """Capitalize first character."""
        from everyshape.types.str.ops import CapitalizeOp

        return cast("StrType", self._wrap_string_result(CapitalizeOp(self)))

    def swapcase(self) -> StrType:
        """Swap case."""
        from everyshape.types.str.ops import SwapCaseOp

        return cast("StrType", self._wrap_string_result(SwapCaseOp(self)))

    # Stripping
    def strip(self, chars: str | Term | None = None) -> StrType:
        """Strip whitespace or chars."""
        from everyshape.types.str.ops import StripOp

        if chars is not None:
            return cast("StrType", self._wrap_string_result(StripOp(self, literal(chars))))
        return cast("StrType", self._wrap_string_result(StripOp(self)))

    def lstrip(self, chars: str | Term | None = None) -> StrType:
        """Strip leading whitespace or chars."""
        from everyshape.types.str.ops import LStripOp

        if chars is not None:
            return cast("StrType", self._wrap_string_result(LStripOp(self, literal(chars))))
        return cast("StrType", self._wrap_string_result(LStripOp(self)))

    def rstrip(self, chars: str | Term | None = None) -> StrType:
        """Strip trailing whitespace or chars."""
        from everyshape.types.str.ops import RStripOp

        if chars is not None:
            return cast("StrType", self._wrap_string_result(RStripOp(self, literal(chars))))
        return cast("StrType", self._wrap_string_result(RStripOp(self)))

    # Splitting
    def split(self, sep: str | Term | None = None, maxsplit: int = -1) -> ListType[str]:
        """Split string."""
        from everyshape.types.str.ops import SplitOp

        from ..list.type import ListType

        if sep is not None:
            return ListType(SplitOp(self, literal(sep), maxsplit))
        return ListType(SplitOp(self, None, maxsplit))

    def rsplit(self, sep: str | Term | None = None, maxsplit: int = -1) -> ListType[str]:
        """Right split string."""
        from everyshape.types.str.ops import RSplitOp

        from ..list.type import ListType

        if sep is not None:
            return ListType(RSplitOp(self, literal(sep), maxsplit))
        return ListType(RSplitOp(self, None, maxsplit))

    # Searching
    def find(self, sub: str | Term, start: int = 0, end: int | None = None) -> IntType:
        """Find substring."""
        from everyshape.types.str.ops import FindOp

        from ..int.type import IntType

        return IntType(FindOp(self, literal(sub), start, end))

    def rfind(self, sub: str | Term, start: int = 0, end: int | None = None) -> IntType:
        """Find substring from right."""
        from everyshape.types.str.ops import RFindOp

        from ..int.type import IntType

        return IntType(RFindOp(self, literal(sub), start, end))

    def count_substring(self, sub: str | Term) -> IntType:
        """Count substring occurrences."""
        from everyshape.types.str.ops import CountSubstringOp

        from ..int.type import IntType

        return IntType(CountSubstringOp(self, literal(sub)))

    # Testing
    def startswith(self, prefix: str | Term) -> BoolType:
        """Check if starts with prefix."""
        from everyshape.types.str.ops import StartsWithOp

        from ..bool.type import BoolType

        return BoolType(StartsWithOp(self, literal(prefix)))

    def endswith(self, suffix: str | Term) -> BoolType:
        """Check if ends with suffix."""
        from everyshape.types.str.ops import EndsWithOp

        from ..bool.type import BoolType

        return BoolType(EndsWithOp(self, literal(suffix)))

    def isdigit(self) -> BoolType:
        """Check if all digits."""
        from everyshape.types.str.ops import IsDigitOp

        from ..bool.type import BoolType

        return BoolType(IsDigitOp(self))

    def isalpha(self) -> BoolType:
        """Check if all alphabetic."""
        from everyshape.types.str.ops import IsAlphaOp

        from ..bool.type import BoolType

        return BoolType(IsAlphaOp(self))

    def isalnum(self) -> BoolType:
        """Check if alphanumeric."""
        from everyshape.types.str.ops import IsAlnumOp

        from ..bool.type import BoolType

        return BoolType(IsAlnumOp(self))

    def isspace(self) -> BoolType:
        """Check if all whitespace."""
        from everyshape.types.str.ops import IsSpaceOp

        from ..bool.type import BoolType

        return BoolType(IsSpaceOp(self))

    # Padding
    def center(self, width: int | Term, fillchar: str = " ") -> StrType:
        """Center in width."""
        from everyshape.types.str.ops import CenterOp

        return cast("StrType", self._wrap_string_result(CenterOp(self, literal(width), fillchar)))

    def ljust(self, width: int | Term, fillchar: str = " ") -> StrType:
        """Left justify."""
        from everyshape.types.str.ops import LJustOp

        return cast("StrType", self._wrap_string_result(LJustOp(self, literal(width), fillchar)))

    def rjust(self, width: int | Term, fillchar: str = " ") -> StrType:
        """Right justify."""
        from everyshape.types.str.ops import RJustOp

        return cast("StrType", self._wrap_string_result(RJustOp(self, literal(width), fillchar)))

    def zfill(self, width: int | Term) -> StrType:
        """Zero-fill."""
        from everyshape.types.str.ops import ZFillOp

        return cast("StrType", self._wrap_string_result(ZFillOp(self, literal(width))))

    # Replacing
    def replace(self, old: str | Term, new: str | Term, count: int = -1) -> StrType:
        """Replace substring."""
        from everyshape.types.str.ops import ReplaceOp

        return cast(
            "StrType",
            self._wrap_string_result(ReplaceOp(self, literal(old), literal(new), count)),
        )

    # Encoding
    def encode(self, encoding: str = "utf-8") -> BytesType:
        """Encode string to bytes."""
        from everyshape.types.str.ops import EncodeOp

        from ..bytes.type import BytesType

        return BytesType(EncodeOp(self, encoding))
