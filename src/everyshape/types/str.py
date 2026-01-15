"""String types for Term expressions.

This module provides StrType including all string-specific methods.
StringMethodsBase is merged directly into StrType.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload

from .bases import (
    AddableBase,
    BaseType,
    ComparisonBase,
    ContainableBase,
    LengthableBase,
    LogicalBase,
    SliceableBase,
)


if TYPE_CHECKING:
    from everyshape.term import IntArg, StrArg, Term

    from .bool import BoolType
    from .bytes import BytesType
    from .int import IntType
    from .list import ListType


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
    BaseType[str],
):
    """String type - represents str expressions (literal or computed).

    Supports concatenation, string operations, comparison, and logical operations.

    Example:
        >>> x = StrType("hello")
        >>> y = x + " world"  # Returns StrType
        >>> z = x.upper()  # Returns StrType
    """

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_string_result(self, operand: Term) -> Term:
        return StrType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        return StrType(operand)

    def __add__(self, other: str | StrType) -> StrType:
        from everyshape.ops import AddOp

        return StrType(AddOp(self, other))

    def __radd__(self, other: str) -> StrType:
        from everyshape.ops import AddOp

        return StrType(AddOp(other, self))

    @overload
    def __getitem__(self, key: int) -> StrType: ...
    @overload
    def __getitem__(self, key: slice) -> StrType: ...
    def __getitem__(self, key: int | slice) -> StrType:
        from everyshape.ops import AtOp, SliceOp

        if isinstance(key, slice):
            return StrType(SliceOp(self, key.start, key.stop, key.step))
        return StrType(AtOp(self, key))

    # =========================================================================
    # STRING-SPECIFIC METHODS (merged from StringMethodsBase)
    # =========================================================================

    # Case transformation
    def upper(self) -> StrType:
        """Convert to uppercase."""
        from .str_ops import UpperOp

        return cast("StrType", self._wrap_string_result(UpperOp(self)))

    def lower(self) -> StrType:
        """Convert to lowercase."""
        from .str_ops import LowerOp

        return cast("StrType", self._wrap_string_result(LowerOp(self)))

    def title(self) -> StrType:
        """Convert to title case."""
        from .str_ops import TitleOp

        return cast("StrType", self._wrap_string_result(TitleOp(self)))

    def capitalize(self) -> StrType:
        """Capitalize first character."""
        from .str_ops import CapitalizeOp

        return cast("StrType", self._wrap_string_result(CapitalizeOp(self)))

    def swapcase(self) -> StrType:
        """Swap case."""
        from .str_ops import SwapCaseOp

        return cast("StrType", self._wrap_string_result(SwapCaseOp(self)))

    # Stripping
    def strip(self, chars: StrArg | None = None) -> StrType:
        """Strip whitespace or chars."""
        from .str_ops import StripOp

        if chars is not None:
            return cast("StrType", self._wrap_string_result(StripOp(self, chars)))
        return cast("StrType", self._wrap_string_result(StripOp(self)))

    def lstrip(self, chars: StrArg | None = None) -> StrType:
        """Strip leading whitespace or chars."""
        from .str_ops import LStripOp

        if chars is not None:
            return cast("StrType", self._wrap_string_result(LStripOp(self, chars)))
        return cast("StrType", self._wrap_string_result(LStripOp(self)))

    def rstrip(self, chars: StrArg | None = None) -> StrType:
        """Strip trailing whitespace or chars."""
        from .str_ops import RStripOp

        if chars is not None:
            return cast("StrType", self._wrap_string_result(RStripOp(self, chars)))
        return cast("StrType", self._wrap_string_result(RStripOp(self)))

    # Splitting
    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListType[str]:
        """Split string."""
        from .list import ListType
        from .str_ops import SplitOp

        if sep is not None:
            return ListType(SplitOp(self, sep, maxsplit))
        return ListType(SplitOp(self, None, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListType[str]:
        """Right split string."""
        from .list import ListType
        from .str_ops import RSplitOp

        if sep is not None:
            return ListType(RSplitOp(self, sep, maxsplit))
        return ListType(RSplitOp(self, None, maxsplit))

    # Searching
    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntType:
        """Find substring."""
        from .int import IntType
        from .str_ops import FindOp

        return IntType(FindOp(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntType:
        """Find substring from right."""
        from .int import IntType
        from .str_ops import RFindOp

        return IntType(RFindOp(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntType:
        """Count substring occurrences."""
        from .int import IntType
        from .str_ops import CountSubstringOp

        return IntType(CountSubstringOp(self, sub))

    # Testing
    def startswith(self, prefix: StrArg) -> BoolType:
        """Check if starts with prefix."""
        from .bool import BoolType
        from .str_ops import StartsWithOp

        return BoolType(StartsWithOp(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolType:
        """Check if ends with suffix."""
        from .bool import BoolType
        from .str_ops import EndsWithOp

        return BoolType(EndsWithOp(self, suffix))

    def isdigit(self) -> BoolType:
        """Check if all digits."""
        from .bool import BoolType
        from .str_ops import IsDigitOp

        return BoolType(IsDigitOp(self))

    def isalpha(self) -> BoolType:
        """Check if all alphabetic."""
        from .bool import BoolType
        from .str_ops import IsAlphaOp

        return BoolType(IsAlphaOp(self))

    def isalnum(self) -> BoolType:
        """Check if alphanumeric."""
        from .bool import BoolType
        from .str_ops import IsAlnumOp

        return BoolType(IsAlnumOp(self))

    def isspace(self) -> BoolType:
        """Check if all whitespace."""
        from .bool import BoolType
        from .str_ops import IsSpaceOp

        return BoolType(IsSpaceOp(self))

    # Padding
    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrType:
        """Center in width."""
        from .str_ops import CenterOp

        return cast("StrType", self._wrap_string_result(CenterOp(self, width, fillchar)))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrType:
        """Left justify."""
        from .str_ops import LJustOp

        return cast("StrType", self._wrap_string_result(LJustOp(self, width, fillchar)))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrType:
        """Right justify."""
        from .str_ops import RJustOp

        return cast("StrType", self._wrap_string_result(RJustOp(self, width, fillchar)))

    def zfill(self, width: IntArg) -> StrType:
        """Zero-fill."""
        from .str_ops import ZFillOp

        return cast("StrType", self._wrap_string_result(ZFillOp(self, width)))

    # Replacing
    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrType:
        """Replace substring."""
        from .str_ops import ReplaceOp

        return cast(
            "StrType",
            self._wrap_string_result(ReplaceOp(self, old, new, count)),
        )

    # Encoding
    def encode(self, encoding: StrArg = "utf-8") -> BytesType:
        """Encode string to bytes."""
        from .bytes import BytesType
        from .str_ops import EncodeOp

        return BytesType(EncodeOp(self, encoding))
