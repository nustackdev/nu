"""String ref base combining string traits.

StrRefBase = RefBase[str] + Addable + Comparable + Logical + Lengthable + Sliceable + Containable

Includes all string-specific methods.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, overload

from everybase.traits import Addable, Comparable, Containable, Lengthable, Logical, Sliceable

from .base import RefBase


if TYPE_CHECKING:
    from every import IntArg, StrArg, Term
    from everybase.py import BoolRef, BytesRef, IntRef, ListRef, StrRef


__all__ = [
    "StrRefBase",
]


class StrRefBase(
    Addable[str, "StrRef"],
    Lengthable,
    Sliceable["StrRef"],
    Containable[str],
    Comparable["str | StrRef"],
    Logical["str | StrRef", "BoolRef"],
    RefBase[str],
    ABC,
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
        from everybase.py.str import StrRef

        return StrRef(operand)

    def _wrap_sliceable_result(self, operand: Term) -> StrRef:
        from everybase.py.str import StrRef

        return StrRef(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def __add__(self, other: StrArg) -> StrRef:
        from everybase.morphisms import AddOp
        from everybase.py.str import StrRef

        return StrRef(AddOp(self, other))

    def __radd__(self, other: StrArg) -> StrRef:
        from everybase.morphisms import AddOp
        from everybase.py.str import StrRef

        return StrRef(AddOp(other, self))

    @overload
    def __getitem__(self, key: IntArg) -> StrRef: ...
    @overload
    def __getitem__(self, key: slice) -> StrRef: ...
    def __getitem__(self, key: IntArg | slice) -> StrRef:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.py.str import StrRef

        if isinstance(key, slice):
            return StrRef(SliceOp(self, key.start, key.stop, key.step))
        return StrRef(AtOp(self, key))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> StrRef:
        """Convert to uppercase."""
        from everybase.morphisms.str_ops import UpperOp
        from everybase.py.str import StrRef

        return StrRef(UpperOp(self))

    def lower(self) -> StrRef:
        """Convert to lowercase."""
        from everybase.morphisms.str_ops import LowerOp
        from everybase.py.str import StrRef

        return StrRef(LowerOp(self))

    def title(self) -> StrRef:
        """Convert to title case."""
        from everybase.morphisms.str_ops import TitleOp
        from everybase.py.str import StrRef

        return StrRef(TitleOp(self))

    def capitalize(self) -> StrRef:
        """Capitalize first character."""
        from everybase.morphisms.str_ops import CapitalizeOp
        from everybase.py.str import StrRef

        return StrRef(CapitalizeOp(self))

    def swapcase(self) -> StrRef:
        """Swap case."""
        from everybase.morphisms.str_ops import SwapCaseOp
        from everybase.py.str import StrRef

        return StrRef(SwapCaseOp(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> StrRef:
        """Strip whitespace or chars."""
        from everybase.morphisms.str_ops import StripOp
        from everybase.py.str import StrRef

        if chars is not None:
            return StrRef(StripOp(self, chars))
        return StrRef(StripOp(self))

    def lstrip(self, chars: StrArg | None = None) -> StrRef:
        """Strip leading whitespace or chars."""
        from everybase.morphisms.str_ops import LStripOp
        from everybase.py.str import StrRef

        if chars is not None:
            return StrRef(LStripOp(self, chars))
        return StrRef(LStripOp(self))

    def rstrip(self, chars: StrArg | None = None) -> StrRef:
        """Strip trailing whitespace or chars."""
        from everybase.morphisms.str_ops import RStripOp
        from everybase.py.str import StrRef

        if chars is not None:
            return StrRef(RStripOp(self, chars))
        return StrRef(RStripOp(self))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListRef:
        """Split string."""
        from everybase.morphisms.str_ops import SplitOp
        from everybase.py.list import ListRef

        if sep is not None:
            return ListRef(SplitOp(self, sep, maxsplit))
        return ListRef(SplitOp(self, maxsplit=maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListRef:
        """Right split string."""
        from everybase.morphisms.str_ops import RSplitOp
        from everybase.py.list import ListRef

        if sep is not None:
            return ListRef(RSplitOp(self, sep, maxsplit))
        return ListRef(RSplitOp(self, maxsplit=maxsplit))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntRef:
        """Find substring."""
        from everybase.morphisms.str_ops import FindOp
        from everybase.py.int import IntRef

        return IntRef(FindOp(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntRef:
        """Find substring from right."""
        from everybase.morphisms.str_ops import RFindOp
        from everybase.py.int import IntRef

        return IntRef(RFindOp(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntRef:
        """Count substring occurrences."""
        from everybase.morphisms.str_ops import CountSubstringOp
        from everybase.py.int import IntRef

        return IntRef(CountSubstringOp(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> BoolRef:
        """Check if starts with prefix."""
        from everybase.morphisms.str_ops import StartsWithOp
        from everybase.py.bool import BoolRef

        return BoolRef(StartsWithOp(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolRef:
        """Check if ends with suffix."""
        from everybase.morphisms.str_ops import EndsWithOp
        from everybase.py.bool import BoolRef

        return BoolRef(EndsWithOp(self, suffix))

    def isdigit(self) -> BoolRef:
        """Check if all digits."""
        from everybase.morphisms.str_ops import IsDigitOp
        from everybase.py.bool import BoolRef

        return BoolRef(IsDigitOp(self))

    def isalpha(self) -> BoolRef:
        """Check if all alphabetic."""
        from everybase.morphisms.str_ops import IsAlphaOp
        from everybase.py.bool import BoolRef

        return BoolRef(IsAlphaOp(self))

    def isalnum(self) -> BoolRef:
        """Check if alphanumeric."""
        from everybase.morphisms.str_ops import IsAlnumOp
        from everybase.py.bool import BoolRef

        return BoolRef(IsAlnumOp(self))

    def isspace(self) -> BoolRef:
        """Check if all whitespace."""
        from everybase.morphisms.str_ops import IsSpaceOp
        from everybase.py.bool import BoolRef

        return BoolRef(IsSpaceOp(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrRef:
        """Center in width."""
        from everybase.morphisms.str_ops import CenterOp
        from everybase.py.str import StrRef

        return StrRef(CenterOp(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrRef:
        """Left justify."""
        from everybase.morphisms.str_ops import LJustOp
        from everybase.py.str import StrRef

        return StrRef(LJustOp(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrRef:
        """Right justify."""
        from everybase.morphisms.str_ops import RJustOp
        from everybase.py.str import StrRef

        return StrRef(RJustOp(self, width, fillchar))

    def zfill(self, width: IntArg) -> StrRef:
        """Zero-fill."""
        from everybase.morphisms.str_ops import ZFillOp
        from everybase.py.str import StrRef

        return StrRef(ZFillOp(self, width))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrRef:
        """Replace substring."""
        from everybase.morphisms.str_ops import ReplaceOp
        from everybase.py.str import StrRef

        return StrRef(ReplaceOp(self, old, new, count))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> BytesRef:
        """Encode string to bytes."""
        from everybase.morphisms.str_ops import EncodeOp
        from everybase.py.bytes import BytesRef

        return BytesRef(EncodeOp(self, encoding))
