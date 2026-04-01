"""String ref base combining string traits.

StrType = Object[str] + Addable + Comparable + Logical + Sliceable

Includes all string-specific methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ...capabilities import (
    AddableBase,
    ComparableBase,
    LogicalBase,
    SliceableBase,
)
from ..object import Object


if TYPE_CHECKING:
    from nu.terms import IntArg, StrArg, Term

    from ...values import BoolValue, BytesValue, IntValue, ListValue, StrValue


__all__ = [
    "StrType",
]


class StrType(
    AddableBase["StrArg", "StrValue"],
    SliceableBase["StrValue"],
    ComparableBase["StrArg"],
    LogicalBase["StrArg", "BoolValue"],
    Object[str],
):
    """Abstract base for string refs.

    Combines:
    - Addable: + (concatenation)
    - Sliceable: slice()
    - Comparable: >, <, >=, <=, eq(), ne(), is_()
    - Logical: and_(), or_(), not_(), bool_()

    Standalone functions: Len(), Contains() in abc.fn

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
        from ...values import StrValue

        return StrValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> StrValue:
        from ...values import StrValue

        return StrValue(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def __add__(self, other: StrArg) -> StrValue:
        from nu.ops import AddOp
        from ...values import StrValue

        return StrValue(AddOp(self, other))

    def __radd__(self, other: StrArg) -> StrValue:
        from nu.ops import AddOp
        from ...values import StrValue

        return StrValue(AddOp(other, self))

    @overload
    def __getitem__(self, key: IntArg) -> StrValue: ...
    @overload
    def __getitem__(self, key: slice) -> StrValue: ...
    def __getitem__(self, key: IntArg | slice) -> StrValue:
        from nu.ops import AtOp, SliceOp
        from ...values import StrValue

        if isinstance(key, slice):
            return StrValue(SliceOp(self, key.start, key.stop, key.step))
        return StrValue(AtOp(self, key))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> StrValue:
        """Convert to uppercase."""
        from nu.ops.builtins.str_ import UpperOp
        from ...values import StrValue

        return StrValue(UpperOp(self))

    def lower(self) -> StrValue:
        """Convert to lowercase."""
        from nu.ops.builtins.str_ import LowerOp
        from ...values import StrValue

        return StrValue(LowerOp(self))

    def title(self) -> StrValue:
        """Convert to title case."""
        from nu.ops.builtins.str_ import TitleOp
        from ...values import StrValue

        return StrValue(TitleOp(self))

    def capitalize(self) -> StrValue:
        """Capitalize first character."""
        from nu.ops.builtins.str_ import CapitalizeOp
        from ...values import StrValue

        return StrValue(CapitalizeOp(self))

    def swapcase(self) -> StrValue:
        """Swap case."""
        from nu.ops.builtins.str_ import SwapCaseOp
        from ...values import StrValue

        return StrValue(SwapCaseOp(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> StrValue:
        """Strip whitespace or chars."""
        from nu.ops.builtins.str_ import StripOp
        from ...values import StrValue

        return StrValue(StripOp(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> StrValue:
        """Strip leading whitespace or chars."""
        from nu.ops.builtins.str_ import LStripOp
        from ...values import StrValue

        return StrValue(LStripOp(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> StrValue:
        """Strip trailing whitespace or chars."""
        from nu.ops.builtins.str_ import RStripOp
        from ...values import StrValue

        return StrValue(RStripOp(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListValue:
        """Split string."""
        from nu.ops.builtins.str_ import SplitOp
        from ...values import ListValue

        return ListValue(SplitOp(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListValue:
        """Right split string."""
        from nu.ops.builtins.str_ import RSplitOp
        from ...values import ListValue

        return ListValue(RSplitOp(self, sep, maxsplit))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntValue:
        """Find substring."""
        from nu.ops.builtins.str_ import FindOp
        from ...values import IntValue

        return IntValue(FindOp(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntValue:
        """Find substring from right."""
        from nu.ops.builtins.str_ import RFindOp
        from ...values import IntValue

        return IntValue(RFindOp(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntValue:
        """Count substring occurrences."""
        from nu.ops.builtins.str_ import CountSubstringOp
        from ...values import IntValue

        return IntValue(CountSubstringOp(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> BoolValue:
        """Check if starts with prefix."""
        from nu.ops.builtins.str_ import StartsWithOp
        from ...values import BoolValue

        return BoolValue(StartsWithOp(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolValue:
        """Check if ends with suffix."""
        from nu.ops.builtins.str_ import EndsWithOp
        from ...values import BoolValue

        return BoolValue(EndsWithOp(self, suffix))

    def isdigit(self) -> BoolValue:
        """Check if all digits."""
        from nu.ops.builtins.str_ import IsDigitOp
        from ...values import BoolValue

        return BoolValue(IsDigitOp(self))

    def isalpha(self) -> BoolValue:
        """Check if all alphabetic."""
        from nu.ops.builtins.str_ import IsAlphaOp
        from ...values import BoolValue

        return BoolValue(IsAlphaOp(self))

    def isalnum(self) -> BoolValue:
        """Check if alphanumeric."""
        from nu.ops.builtins.str_ import IsAlnumOp
        from ...values import BoolValue

        return BoolValue(IsAlnumOp(self))

    def isspace(self) -> BoolValue:
        """Check if all whitespace."""
        from nu.ops.builtins.str_ import IsSpaceOp
        from ...values import BoolValue

        return BoolValue(IsSpaceOp(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrValue:
        """Center in width."""
        from nu.ops.builtins.str_ import CenterOp
        from ...values import StrValue

        return StrValue(CenterOp(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrValue:
        """Left justify."""
        from nu.ops.builtins.str_ import LJustOp
        from ...values import StrValue

        return StrValue(LJustOp(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrValue:
        """Right justify."""
        from nu.ops.builtins.str_ import RJustOp
        from ...values import StrValue

        return StrValue(RJustOp(self, width, fillchar))

    def zfill(self, width: IntArg) -> StrValue:
        """Zero-fill."""
        from nu.ops.builtins.str_ import ZFillOp
        from ...values import StrValue

        return StrValue(ZFillOp(self, width))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrValue:
        """Replace substring."""
        from nu.ops.builtins.str_ import ReplaceOp
        from ...values import StrValue

        return StrValue(ReplaceOp(self, old, new, count))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> BytesValue:
        """Encode string to bytes."""
        from nu.ops.builtins.str_ import EncodeOp
        from ...values import BytesValue

        return BytesValue(EncodeOp(self, encoding))
