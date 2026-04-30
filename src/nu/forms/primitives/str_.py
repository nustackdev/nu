"""StrForm - string interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import Form, TypedNu


if TYPE_CHECKING:
    from nu.terms import IntArg, StrArg

    from .bool_ import BoolForm
    from .int_ import IntForm


__all__ = [
    "StrForm",
]


class StrForm(Form, TypedNu[str]):
    """String interface. Addable + sliceable + comparable + logical + string methods."""

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: StrArg) -> StrForm:
        from nu import Add

        return StrForm(Add(self, other))

    def __radd__(self, other: StrArg) -> StrForm:
        from nu import Add

        return StrForm(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> StrForm: ...
    @overload
    def __getitem__(self, key: slice) -> StrForm: ...
    def __getitem__(self, key: IntArg | slice) -> StrForm:
        from nu import At, Slice

        if isinstance(key, slice):
            return StrForm(Slice(self, key.start, key.stop, key.step))
        return StrForm(At(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: StrArg) -> BoolForm:
        from nu import Gt

        from .bool_ import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: StrArg) -> BoolForm:
        from nu import Lt

        from .bool_ import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: StrArg) -> BoolForm:
        from nu import Ge

        from .bool_ import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: StrArg) -> BoolForm:
        from nu import Le

        from .bool_ import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: StrArg) -> BoolForm:
        from nu import Eq

        from .bool_ import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: StrArg) -> BoolForm:
        from nu import Ne

        from .bool_ import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: StrArg) -> BoolForm:
        from nu import IdComp

        from .bool_ import BoolForm

        return BoolForm(IdComp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: StrArg) -> BoolForm:
        from nu import And

        from .bool_ import BoolForm

        return BoolForm(And(self, other))

    def or_(self, other: StrArg) -> BoolForm:
        from nu import Or

        from .bool_ import BoolForm

        return BoolForm(Or(self, other))

    def not_(self) -> BoolForm:
        from nu import Not

        from .bool_ import BoolForm

        return BoolForm(Not(self))

    def bool_(self) -> BoolForm:
        from nu import Bool

        from .bool_ import BoolForm

        return BoolForm(Bool(self))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> StrForm:
        from .str_ops import UpperOp

        return StrForm(UpperOp(self))

    def lower(self) -> StrForm:
        from .str_ops import LowerOp

        return StrForm(LowerOp(self))

    def title(self) -> StrForm:
        from .str_ops import TitleOp

        return StrForm(TitleOp(self))

    def capitalize(self) -> StrForm:
        from .str_ops import CapitalizeOp

        return StrForm(CapitalizeOp(self))

    def swapcase(self) -> StrForm:
        from .str_ops import SwapCaseOp

        return StrForm(SwapCaseOp(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> StrForm:
        from .str_ops import StripOp

        return StrForm(StripOp(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> StrForm:
        from .str_ops import LStripOp

        return StrForm(LStripOp(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> StrForm:
        from .str_ops import RStripOp

        return StrForm(RStripOp(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListForm:
        from ..forms.collections.list_ import ListForm
        from .str_ops import SplitOp

        return ListForm(SplitOp(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListForm:
        from ..forms.collections.list_ import ListForm
        from .str_ops import RSplitOp

        return ListForm(RSplitOp(self, sep, maxsplit))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        from .int_ import IntForm
        from .str_ops import FindOp

        return IntForm(FindOp(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        from .int_ import IntForm
        from .str_ops import RFindOp

        return IntForm(RFindOp(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntForm:
        from .int_ import IntForm
        from .str_ops import CountSubstringOp

        return IntForm(CountSubstringOp(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> BoolForm:
        from .bool_ import BoolForm
        from .str_ops import StartsWithOp

        return BoolForm(StartsWithOp(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolForm:
        from .bool_ import BoolForm
        from .str_ops import EndsWithOp

        return BoolForm(EndsWithOp(self, suffix))

    def isdigit(self) -> BoolForm:
        from .bool_ import BoolForm
        from .str_ops import IsDigitOp

        return BoolForm(IsDigitOp(self))

    def isalpha(self) -> BoolForm:
        from .bool_ import BoolForm
        from .str_ops import IsAlphaOp

        return BoolForm(IsAlphaOp(self))

    def isalnum(self) -> BoolForm:
        from .bool_ import BoolForm
        from .str_ops import IsAlnumOp

        return BoolForm(IsAlnumOp(self))

    def isspace(self) -> BoolForm:
        from .bool_ import BoolForm
        from .str_ops import IsSpaceOp

        return BoolForm(IsSpaceOp(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrForm:
        from .str_ops import CenterOp

        return StrForm(CenterOp(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrForm:
        from .str_ops import LJustOp

        return StrForm(LJustOp(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrForm:
        from .str_ops import RJustOp

        return StrForm(RJustOp(self, width, fillchar))

    def zfill(self, width: IntArg) -> StrForm:
        from .str_ops import ZFillOp

        return StrForm(ZFillOp(self, width))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrForm:
        from .str_ops import ReplaceOp

        return StrForm(ReplaceOp(self, old, new, count))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> BytesForm:
        from .bytes_ import BytesForm
        from .str_ops import EncodeOp

        return BytesForm(EncodeOp(self, encoding))

    # =========================================================================
    # JOINING
    # =========================================================================

    def join(self, iterable: object) -> StrForm:
        """Join iterable elements with this string as separator."""
        from .str_ops import JoinOp

        return StrForm(JoinOp(self, iterable))
