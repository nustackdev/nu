"""StrI - string interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from nu.terms import IntArg, StrArg

    from .bool_ import BoolI
    from .int_ import IntI


__all__ = [
    "StrI",
]


class StrI(Interface, TypedNu[str]):
    """String interface. Addable + sliceable + comparable + logical + string methods."""

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: StrArg) -> StrI:
        from nu import Add

        return StrI(Add(self, other))

    def __radd__(self, other: StrArg) -> StrI:
        from nu import Add

        return StrI(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> StrI: ...
    @overload
    def __getitem__(self, key: slice) -> StrI: ...
    def __getitem__(self, key: IntArg | slice) -> StrI:
        from nu import At, Slice

        if isinstance(key, slice):
            return StrI(Slice(self, key.start, key.stop, key.step))
        return StrI(At(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: StrArg) -> BoolI:
        from nu import Gt

        from .bool_ import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: StrArg) -> BoolI:
        from nu import Lt

        from .bool_ import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: StrArg) -> BoolI:
        from nu import Ge

        from .bool_ import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: StrArg) -> BoolI:
        from nu import Le

        from .bool_ import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: StrArg) -> BoolI:
        from nu import Eq

        from .bool_ import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: StrArg) -> BoolI:
        from nu import Ne

        from .bool_ import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: StrArg) -> BoolI:
        from nu import IdComp

        from .bool_ import BoolI

        return BoolI(IdComp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: StrArg) -> BoolI:
        from nu import And

        from .bool_ import BoolI

        return BoolI(And(self, other))

    def or_(self, other: StrArg) -> BoolI:
        from nu import Or

        from .bool_ import BoolI

        return BoolI(Or(self, other))

    def not_(self) -> BoolI:
        from nu import Not

        from .bool_ import BoolI

        return BoolI(Not(self))

    def bool_(self) -> BoolI:
        from nu import Bool

        from .bool_ import BoolI

        return BoolI(Bool(self))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> StrI:
        from .str_ops import UpperOp

        return StrI(UpperOp(self))

    def lower(self) -> StrI:
        from .str_ops import LowerOp

        return StrI(LowerOp(self))

    def title(self) -> StrI:
        from .str_ops import TitleOp

        return StrI(TitleOp(self))

    def capitalize(self) -> StrI:
        from .str_ops import CapitalizeOp

        return StrI(CapitalizeOp(self))

    def swapcase(self) -> StrI:
        from .str_ops import SwapCaseOp

        return StrI(SwapCaseOp(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> StrI:
        from .str_ops import StripOp

        return StrI(StripOp(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> StrI:
        from .str_ops import LStripOp

        return StrI(LStripOp(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> StrI:
        from .str_ops import RStripOp

        return StrI(RStripOp(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListI:
        from ..collections.list_ import ListI
        from .str_ops import SplitOp

        return ListI(SplitOp(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListI:
        from ..collections.list_ import ListI
        from .str_ops import RSplitOp

        return ListI(RSplitOp(self, sep, maxsplit))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntI:
        from .int_ import IntI
        from .str_ops import FindOp

        return IntI(FindOp(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntI:
        from .int_ import IntI
        from .str_ops import RFindOp

        return IntI(RFindOp(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntI:
        from .int_ import IntI
        from .str_ops import CountSubstringOp

        return IntI(CountSubstringOp(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> BoolI:
        from .bool_ import BoolI
        from .str_ops import StartsWithOp

        return BoolI(StartsWithOp(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolI:
        from .bool_ import BoolI
        from .str_ops import EndsWithOp

        return BoolI(EndsWithOp(self, suffix))

    def isdigit(self) -> BoolI:
        from .bool_ import BoolI
        from .str_ops import IsDigitOp

        return BoolI(IsDigitOp(self))

    def isalpha(self) -> BoolI:
        from .bool_ import BoolI
        from .str_ops import IsAlphaOp

        return BoolI(IsAlphaOp(self))

    def isalnum(self) -> BoolI:
        from .bool_ import BoolI
        from .str_ops import IsAlnumOp

        return BoolI(IsAlnumOp(self))

    def isspace(self) -> BoolI:
        from .bool_ import BoolI
        from .str_ops import IsSpaceOp

        return BoolI(IsSpaceOp(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrI:
        from .str_ops import CenterOp

        return StrI(CenterOp(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrI:
        from .str_ops import LJustOp

        return StrI(LJustOp(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrI:
        from .str_ops import RJustOp

        return StrI(RJustOp(self, width, fillchar))

    def zfill(self, width: IntArg) -> StrI:
        from .str_ops import ZFillOp

        return StrI(ZFillOp(self, width))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrI:
        from .str_ops import ReplaceOp

        return StrI(ReplaceOp(self, old, new, count))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> BytesI:
        from .bytes_ import BytesI
        from .str_ops import EncodeOp

        return BytesI(EncodeOp(self, encoding))

    # =========================================================================
    # JOINING
    # =========================================================================

    def join(self, iterable: object) -> StrI:
        """Join iterable elements with this string as separator."""
        from .str_ops import JoinOp

        return StrI(JoinOp(self, iterable))
