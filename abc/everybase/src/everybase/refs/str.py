"""String ref base combining string traits.

StrRefBase = RefBase[str] + Addable + Comparable + Logical + Lengthable + Sliceable + Containable

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

from ._base import RefBase


if TYPE_CHECKING:
    from everyabc import IntArg, StrArg, Term
    from everybase.py import BoolRef, BytesRef, IntRef, ListRef, StrRef


__all__ = [
    "StrRefBase",
]


class StrRefBase(
    AddableBase[str, "StrRef"],
    LengthableBase,
    SliceableBase["StrRef"],
    ContainableBase[str],
    ComparableBase["str | StrRef"],
    LogicalBase["str | StrRef", "BoolRef"],
    RefBase[str],
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

    def _wrap_arithmetic_result(self, operand: Term) -> StrRef:
        from everybase.py import StrRef

        return StrRef(operand)

    def _wrap_sliceable_result(self, operand: Term) -> StrRef:
        from everybase.py import StrRef

        return StrRef(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py import BoolRef

        return BoolRef(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py import BoolRef

        return BoolRef(operand)

    def __add__(self, other: StrArg) -> StrRef:
        from everybase.morphisms import AddOp
        from everybase.py import StrRef

        return StrRef(AddOp(self, other))

    def __radd__(self, other: StrArg) -> StrRef:
        from everybase.morphisms import AddOp
        from everybase.py import StrRef

        return StrRef(AddOp(other, self))

    @overload
    def __getitem__(self, key: IntArg) -> StrRef: ...
    @overload
    def __getitem__(self, key: slice) -> StrRef: ...
    def __getitem__(self, key: IntArg | slice) -> StrRef:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.py import StrRef

        if isinstance(key, slice):
            return StrRef(SliceOp(self, key.start, key.stop, key.step))
        return StrRef(AtOp(self, key))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> StrRef:
        """Convert to uppercase."""
        from everybase.morphisms.type_str import UpperOp
        from everybase.py import StrRef

        return StrRef(UpperOp(self))

    def lower(self) -> StrRef:
        """Convert to lowercase."""
        from everybase.morphisms.type_str import LowerOp
        from everybase.py import StrRef

        return StrRef(LowerOp(self))

    def title(self) -> StrRef:
        """Convert to title case."""
        from everybase.morphisms.type_str import TitleOp
        from everybase.py import StrRef

        return StrRef(TitleOp(self))

    def capitalize(self) -> StrRef:
        """Capitalize first character."""
        from everybase.morphisms.type_str import CapitalizeOp
        from everybase.py import StrRef

        return StrRef(CapitalizeOp(self))

    def swapcase(self) -> StrRef:
        """Swap case."""
        from everybase.morphisms.type_str import SwapCaseOp
        from everybase.py import StrRef

        return StrRef(SwapCaseOp(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> StrRef:
        """Strip whitespace or chars."""
        from everybase.morphisms.type_str import StripOp
        from everybase.py import StrRef

        return StrRef(StripOp(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> StrRef:
        """Strip leading whitespace or chars."""
        from everybase.morphisms.type_str import LStripOp
        from everybase.py import StrRef

        return StrRef(LStripOp(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> StrRef:
        """Strip trailing whitespace or chars."""
        from everybase.morphisms.type_str import RStripOp
        from everybase.py import StrRef

        return StrRef(RStripOp(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListRef:
        """Split string."""
        from everybase.morphisms.type_str import SplitOp
        from everybase.py import ListRef

        return ListRef(SplitOp(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListRef:
        """Right split string."""
        from everybase.morphisms.type_str import RSplitOp
        from everybase.py import ListRef

        return ListRef(RSplitOp(self, sep, maxsplit))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntRef:
        """Find substring."""
        from everybase.morphisms.type_str import FindOp
        from everybase.py import IntRef

        return IntRef(FindOp(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntRef:
        """Find substring from right."""
        from everybase.morphisms.type_str import RFindOp
        from everybase.py import IntRef

        return IntRef(RFindOp(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntRef:
        """Count substring occurrences."""
        from everybase.morphisms.type_str import CountSubstringOp
        from everybase.py import IntRef

        return IntRef(CountSubstringOp(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> BoolRef:
        """Check if starts with prefix."""
        from everybase.morphisms.type_str import StartsWithOp
        from everybase.py import BoolRef

        return BoolRef(StartsWithOp(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolRef:
        """Check if ends with suffix."""
        from everybase.morphisms.type_str import EndsWithOp
        from everybase.py import BoolRef

        return BoolRef(EndsWithOp(self, suffix))

    def isdigit(self) -> BoolRef:
        """Check if all digits."""
        from everybase.morphisms.type_str import IsDigitOp
        from everybase.py import BoolRef

        return BoolRef(IsDigitOp(self))

    def isalpha(self) -> BoolRef:
        """Check if all alphabetic."""
        from everybase.morphisms.type_str import IsAlphaOp
        from everybase.py import BoolRef

        return BoolRef(IsAlphaOp(self))

    def isalnum(self) -> BoolRef:
        """Check if alphanumeric."""
        from everybase.morphisms.type_str import IsAlnumOp
        from everybase.py import BoolRef

        return BoolRef(IsAlnumOp(self))

    def isspace(self) -> BoolRef:
        """Check if all whitespace."""
        from everybase.morphisms.type_str import IsSpaceOp
        from everybase.py import BoolRef

        return BoolRef(IsSpaceOp(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrRef:
        """Center in width."""
        from everybase.morphisms.type_str import CenterOp
        from everybase.py import StrRef

        return StrRef(CenterOp(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrRef:
        """Left justify."""
        from everybase.morphisms.type_str import LJustOp
        from everybase.py import StrRef

        return StrRef(LJustOp(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrRef:
        """Right justify."""
        from everybase.morphisms.type_str import RJustOp
        from everybase.py import StrRef

        return StrRef(RJustOp(self, width, fillchar))

    def zfill(self, width: IntArg) -> StrRef:
        """Zero-fill."""
        from everybase.morphisms.type_str import ZFillOp
        from everybase.py import StrRef

        return StrRef(ZFillOp(self, width))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrRef:
        """Replace substring."""
        from everybase.morphisms.type_str import ReplaceOp
        from everybase.py import StrRef

        return StrRef(ReplaceOp(self, old, new, count))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> BytesRef:
        """Encode string to bytes."""
        from everybase.morphisms.type_str import EncodeOp
        from everybase.py import BytesRef

        return BytesRef(EncodeOp(self, encoding))
