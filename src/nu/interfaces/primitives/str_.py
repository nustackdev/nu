"""StrI - string interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.interfaces.interface import Interface


if TYPE_CHECKING:
    from nu.terms import IntArg, StrArg

    from .bool_ import BoolI
    from .int_ import IntI


__all__ = [
    "StrI",
]


class StrI(Interface[str]):
    """String interface. Addable + sliceable + comparable + logical + string methods."""

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: StrArg) -> StrI:
        from nu.ops import AddOp

        return StrI(AddOp(self, other))

    def __radd__(self, other: StrArg) -> StrI:
        from nu.ops import AddOp

        return StrI(AddOp(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> StrI: ...
    @overload
    def __getitem__(self, key: slice) -> StrI: ...
    def __getitem__(self, key: IntArg | slice) -> StrI:
        from nu.ops import AtOp, SliceOp

        if isinstance(key, slice):
            return StrI(SliceOp(self, key.start, key.stop, key.step))
        return StrI(AtOp(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: StrArg) -> BoolI:
        from nu.ops import GtOp

        from .bool_ import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: StrArg) -> BoolI:
        from nu.ops import LtOp

        from .bool_ import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: StrArg) -> BoolI:
        from nu.ops import GeOp

        from .bool_ import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: StrArg) -> BoolI:
        from nu.ops import LeOp

        from .bool_ import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: StrArg) -> BoolI:
        from nu.ops import EqOp

        from .bool_ import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: StrArg) -> BoolI:
        from nu.ops import NeOp

        from .bool_ import BoolI

        return BoolI(NeOp(self, other))

    def is_(self, other: StrArg) -> BoolI:
        from nu.ops import IdCompOp

        from .bool_ import BoolI

        return BoolI(IdCompOp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: StrArg) -> BoolI:
        from nu.ops import AndOp

        from .bool_ import BoolI

        return BoolI(AndOp(self, other))

    def or_(self, other: StrArg) -> BoolI:
        from nu.ops import OrOp

        from .bool_ import BoolI

        return BoolI(OrOp(self, other))

    def not_(self) -> BoolI:
        from nu.ops import NotOp

        from .bool_ import BoolI

        return BoolI(NotOp(self))

    def bool_(self) -> BoolI:
        from nu.ops import BoolOp

        from .bool_ import BoolI

        return BoolI(BoolOp(self))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> StrI:
        from nu.ops.builtins.str_ import UpperOp

        return StrI(UpperOp(self))

    def lower(self) -> StrI:
        from nu.ops.builtins.str_ import LowerOp

        return StrI(LowerOp(self))

    def title(self) -> StrI:
        from nu.ops.builtins.str_ import TitleOp

        return StrI(TitleOp(self))

    def capitalize(self) -> StrI:
        from nu.ops.builtins.str_ import CapitalizeOp

        return StrI(CapitalizeOp(self))

    def swapcase(self) -> StrI:
        from nu.ops.builtins.str_ import SwapCaseOp

        return StrI(SwapCaseOp(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> StrI:
        from nu.ops.builtins.str_ import StripOp

        return StrI(StripOp(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> StrI:
        from nu.ops.builtins.str_ import LStripOp

        return StrI(LStripOp(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> StrI:
        from nu.ops.builtins.str_ import RStripOp

        return StrI(RStripOp(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListI:
        from nu.ops.builtins.str_ import SplitOp

        from nu.interfaces.collections.list_ import ListI

        return ListI(SplitOp(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListI:
        from nu.ops.builtins.str_ import RSplitOp

        from nu.interfaces.collections.list_ import ListI

        return ListI(RSplitOp(self, sep, maxsplit))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntI:
        from nu.ops.builtins.str_ import FindOp

        from .int_ import IntI

        return IntI(FindOp(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntI:
        from nu.ops.builtins.str_ import RFindOp

        from .int_ import IntI

        return IntI(RFindOp(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntI:
        from nu.ops.builtins.str_ import CountSubstringOp

        from .int_ import IntI

        return IntI(CountSubstringOp(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> BoolI:
        from nu.ops.builtins.str_ import StartsWithOp

        from .bool_ import BoolI

        return BoolI(StartsWithOp(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolI:
        from nu.ops.builtins.str_ import EndsWithOp

        from .bool_ import BoolI

        return BoolI(EndsWithOp(self, suffix))

    def isdigit(self) -> BoolI:
        from nu.ops.builtins.str_ import IsDigitOp

        from .bool_ import BoolI

        return BoolI(IsDigitOp(self))

    def isalpha(self) -> BoolI:
        from nu.ops.builtins.str_ import IsAlphaOp

        from .bool_ import BoolI

        return BoolI(IsAlphaOp(self))

    def isalnum(self) -> BoolI:
        from nu.ops.builtins.str_ import IsAlnumOp

        from .bool_ import BoolI

        return BoolI(IsAlnumOp(self))

    def isspace(self) -> BoolI:
        from nu.ops.builtins.str_ import IsSpaceOp

        from .bool_ import BoolI

        return BoolI(IsSpaceOp(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrI:
        from nu.ops.builtins.str_ import CenterOp

        return StrI(CenterOp(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrI:
        from nu.ops.builtins.str_ import LJustOp

        return StrI(LJustOp(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrI:
        from nu.ops.builtins.str_ import RJustOp

        return StrI(RJustOp(self, width, fillchar))

    def zfill(self, width: IntArg) -> StrI:
        from nu.ops.builtins.str_ import ZFillOp

        return StrI(ZFillOp(self, width))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrI:
        from nu.ops.builtins.str_ import ReplaceOp

        return StrI(ReplaceOp(self, old, new, count))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> BytesI:
        from nu.ops.builtins.str_ import EncodeOp

        from .bytes_ import BytesI

        return BytesI(EncodeOp(self, encoding))
