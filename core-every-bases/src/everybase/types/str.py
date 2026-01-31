"""String ref base combining string traits.

StrType = TypeBase[str] + Addable + Comparable + Logical + Lengthable + Sliceable + Containable

Includes all string-specific methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everybase.capabilities import (
    AddableBase,
    ComparableBase,
    ContainableBase,
    LengthableBase,
    LogicalBase,
    SliceableBase,
)

from ._base import TypeBase


if TYPE_CHECKING:
    from everyabc import IntArg, StrArg, Term
    from everybase.values import BoolValue, BytesValue, IntValue, ListValue, StrValue


__all__ = [
    "StrType",
]


class StrType(
    AddableBase[str, "StrValue"],
    LengthableBase,
    SliceableBase["StrValue"],
    ContainableBase[str],
    ComparableBase["str | StrValue"],
    LogicalBase["str | StrValue", "BoolValue"],
    TypeBase[str],
):
    """Abstract base for string refs.

    Combines:
    - Addable: + (concatenation)
    - Lengthable: len_()
    - Sliceable: slice_()
    - Containable: contains()
    - Comparable: >, <, >=, <=, eq(), ne(), is_()
    - Logical: and_(), or_(), not_(), bool_()

    String-specific methods:
    - Case: upper(), lower(), title(), capitalize(), swapcase()
    - Strip: strip(), lstrip(), rstrip()
    - Split: split(), rsplit()
    - Search: find(), rfind(), count_substring()
    - Test: startswith(), endswith(), isdigit(), isalpha(), isalnum(), isspace()
    - Pad: center(), ljust(), rjust(), zfill()
    - Replace: replace()
    - Encode: encode()
    """

    def _wrap_arithmetic_result(self, operand: Term) -> StrValue:
        from everybase.values import StrValue

        return StrValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> StrValue:
        from everybase.values import StrValue

        return StrValue(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def __add__(self, other: StrArg) -> StrValue:
        from everybase.morphisms import AddOp
        from everybase.values import StrValue

        return StrValue(AddOp(self, other))

    def __radd__(self, other: StrArg) -> StrValue:
        from everybase.morphisms import AddOp
        from everybase.values import StrValue

        return StrValue(AddOp(other, self))

    @overload
    def __getitem__(self, key: IntArg) -> StrValue: ...
    @overload
    def __getitem__(self, key: slice) -> StrValue: ...
    def __getitem__(self, key: IntArg | slice) -> StrValue:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.values import StrValue

        if isinstance(key, slice):
            return StrValue(SliceOp(self, key.start, key.stop, key.step))
        return StrValue(AtOp(self, key))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> StrValue:
        """Convert to uppercase."""
        from everybase.morphisms.type_str import UpperOp
        from everybase.values import StrValue

        return StrValue(UpperOp(self))

    def lower(self) -> StrValue:
        """Convert to lowercase."""
        from everybase.morphisms.type_str import LowerOp
        from everybase.values import StrValue

        return StrValue(LowerOp(self))

    def title(self) -> StrValue:
        """Convert to title case."""
        from everybase.morphisms.type_str import TitleOp
        from everybase.values import StrValue

        return StrValue(TitleOp(self))

    def capitalize(self) -> StrValue:
        """Capitalize first character."""
        from everybase.morphisms.type_str import CapitalizeOp
        from everybase.values import StrValue

        return StrValue(CapitalizeOp(self))

    def swapcase(self) -> StrValue:
        """Swap case."""
        from everybase.morphisms.type_str import SwapCaseOp
        from everybase.values import StrValue

        return StrValue(SwapCaseOp(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> StrValue:
        """Strip whitespace or chars."""
        from everybase.morphisms.type_str import StripOp
        from everybase.values import StrValue

        return StrValue(StripOp(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> StrValue:
        """Strip leading whitespace or chars."""
        from everybase.morphisms.type_str import LStripOp
        from everybase.values import StrValue

        return StrValue(LStripOp(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> StrValue:
        """Strip trailing whitespace or chars."""
        from everybase.morphisms.type_str import RStripOp
        from everybase.values import StrValue

        return StrValue(RStripOp(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListValue:
        """Split string."""
        from everybase.morphisms.type_str import SplitOp
        from everybase.values import ListValue

        return ListValue(SplitOp(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListValue:
        """Right split string."""
        from everybase.morphisms.type_str import RSplitOp
        from everybase.values import ListValue

        return ListValue(RSplitOp(self, sep, maxsplit))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntValue:
        """Find substring."""
        from everybase.morphisms.type_str import FindOp
        from everybase.values import IntValue

        return IntValue(FindOp(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntValue:
        """Find substring from right."""
        from everybase.morphisms.type_str import RFindOp
        from everybase.values import IntValue

        return IntValue(RFindOp(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntValue:
        """Count substring occurrences."""
        from everybase.morphisms.type_str import CountSubstringOp
        from everybase.values import IntValue

        return IntValue(CountSubstringOp(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> BoolValue:
        """Check if starts with prefix."""
        from everybase.morphisms.type_str import StartsWithOp
        from everybase.values import BoolValue

        return BoolValue(StartsWithOp(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolValue:
        """Check if ends with suffix."""
        from everybase.morphisms.type_str import EndsWithOp
        from everybase.values import BoolValue

        return BoolValue(EndsWithOp(self, suffix))

    def isdigit(self) -> BoolValue:
        """Check if all digits."""
        from everybase.morphisms.type_str import IsDigitOp
        from everybase.values import BoolValue

        return BoolValue(IsDigitOp(self))

    def isalpha(self) -> BoolValue:
        """Check if all alphabetic."""
        from everybase.morphisms.type_str import IsAlphaOp
        from everybase.values import BoolValue

        return BoolValue(IsAlphaOp(self))

    def isalnum(self) -> BoolValue:
        """Check if alphanumeric."""
        from everybase.morphisms.type_str import IsAlnumOp
        from everybase.values import BoolValue

        return BoolValue(IsAlnumOp(self))

    def isspace(self) -> BoolValue:
        """Check if all whitespace."""
        from everybase.morphisms.type_str import IsSpaceOp
        from everybase.values import BoolValue

        return BoolValue(IsSpaceOp(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrValue:
        """Center in width."""
        from everybase.morphisms.type_str import CenterOp
        from everybase.values import StrValue

        return StrValue(CenterOp(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrValue:
        """Left justify."""
        from everybase.morphisms.type_str import LJustOp
        from everybase.values import StrValue

        return StrValue(LJustOp(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrValue:
        """Right justify."""
        from everybase.morphisms.type_str import RJustOp
        from everybase.values import StrValue

        return StrValue(RJustOp(self, width, fillchar))

    def zfill(self, width: IntArg) -> StrValue:
        """Zero-fill."""
        from everybase.morphisms.type_str import ZFillOp
        from everybase.values import StrValue

        return StrValue(ZFillOp(self, width))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrValue:
        """Replace substring."""
        from everybase.morphisms.type_str import ReplaceOp
        from everybase.values import StrValue

        return StrValue(ReplaceOp(self, old, new, count))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> BytesValue:
        """Encode string to bytes."""
        from everybase.morphisms.type_str import EncodeOp
        from everybase.values import BytesValue

        return BytesValue(EncodeOp(self, encoding))
