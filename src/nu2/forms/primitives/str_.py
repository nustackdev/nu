"""StrForm - string interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu2.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu2.lang import IntArg, StrArg

    from ..collections.list_ import ListForm
    from .bool_ import BoolForm
    from .bytes_ import BytesForm
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
        from nu2.core import Add

        return StrForm(Add(self, other))

    def __radd__(self, other: StrArg) -> StrForm:
        from nu2.core import Add

        return StrForm(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> StrForm: ...
    @overload
    def __getitem__(self, key: slice) -> StrForm: ...
    def __getitem__(self, key: IntArg | slice) -> StrForm:
        from nu2.core import GetItem, Slice

        if isinstance(key, slice):
            return StrForm(Slice(self, key.start, key.stop, key.step))
        return StrForm(GetItem(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: StrArg) -> BoolForm:
        from nu2.core import Gt

        from .bool_ import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: StrArg) -> BoolForm:
        from nu2.core import Lt

        from .bool_ import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: StrArg) -> BoolForm:
        from nu2.core import Ge

        from .bool_ import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: StrArg) -> BoolForm:
        from nu2.core import Le

        from .bool_ import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: StrArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import Eq

        from .bool_ import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: StrArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import Ne

        from .bool_ import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: StrArg) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import Is

        from .bool_ import BoolForm

        return BoolForm(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: StrArg) -> BoolForm:
        """Logical AND: self AND other."""
        from nu2.core import And

        from .bool_ import BoolForm

        return BoolForm(And(self, other))

    def or_(self, other: StrArg) -> BoolForm:
        """Logical OR: self OR other."""
        from nu2.core import Or

        from .bool_ import BoolForm

        return BoolForm(Or(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu2.core import Not

        from .bool_ import BoolForm

        return BoolForm(Not(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu2.core import Bool

        from .bool_ import BoolForm

        return BoolForm(Bool(self))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> StrForm:
        """Convert to uppercase."""
        from .str_interactions import UpperQuery

        return StrForm(UpperQuery(self))

    def lower(self) -> StrForm:
        """Convert to lowercase."""
        from .str_interactions import LowerQuery

        return StrForm(LowerQuery(self))

    def title(self) -> StrForm:
        """Convert to title case."""
        from .str_interactions import TitleQuery

        return StrForm(TitleQuery(self))

    def capitalize(self) -> StrForm:
        """Capitalize first character."""
        from .str_interactions import CapitalizeQuery

        return StrForm(CapitalizeQuery(self))

    def swapcase(self) -> StrForm:
        """Swap case of all characters."""
        from .str_interactions import SwapCaseQuery

        return StrForm(SwapCaseQuery(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> StrForm:
        """Strip leading and trailing whitespace or chars."""
        from .str_interactions import StripQuery

        return StrForm(StripQuery(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> StrForm:
        """Strip leading whitespace or chars."""
        from .str_interactions import LStripQuery

        return StrForm(LStripQuery(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> StrForm:
        """Strip trailing whitespace or chars."""
        from .str_interactions import RStripQuery

        return StrForm(RStripQuery(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListForm:
        """Split string into list on sep."""
        from ..collections.list_ import ListForm
        from .str_interactions import SplitQuery

        return ListForm(SplitQuery(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> ListForm:
        """Right-split string into list on sep."""
        from ..collections.list_ import ListForm
        from .str_interactions import RSplitQuery

        return ListForm(RSplitQuery(self, sep, maxsplit))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        """Find substring index: str.find(sub, start, end)."""
        from .int_ import IntForm
        from .str_interactions import FindQuery

        return IntForm(FindQuery(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        """Find substring index from right: str.rfind(sub, start, end)."""
        from .int_ import IntForm
        from .str_interactions import RFindQuery

        return IntForm(RFindQuery(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> IntForm:
        """Count non-overlapping occurrences of sub."""
        from .int_ import IntForm
        from .str_interactions import CountSubstringQuery

        return IntForm(CountSubstringQuery(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> BoolForm:
        """Check if string starts with prefix."""
        from .bool_ import BoolForm
        from .str_interactions import StartsWithQuery

        return BoolForm(StartsWithQuery(self, prefix))

    def endswith(self, suffix: StrArg) -> BoolForm:
        """Check if string ends with suffix."""
        from .bool_ import BoolForm
        from .str_interactions import EndsWithQuery

        return BoolForm(EndsWithQuery(self, suffix))

    def isdigit(self) -> BoolForm:
        """Check if all characters are digits."""
        from .bool_ import BoolForm
        from .str_interactions import IsDigitQuery

        return BoolForm(IsDigitQuery(self))

    def isalpha(self) -> BoolForm:
        """Check if all characters are alphabetic."""
        from .bool_ import BoolForm
        from .str_interactions import IsAlphaQuery

        return BoolForm(IsAlphaQuery(self))

    def isalnum(self) -> BoolForm:
        """Check if all characters are alphanumeric."""
        from .bool_ import BoolForm
        from .str_interactions import IsAlnumQuery

        return BoolForm(IsAlnumQuery(self))

    def isspace(self) -> BoolForm:
        """Check if all characters are whitespace."""
        from .bool_ import BoolForm
        from .str_interactions import IsSpaceQuery

        return BoolForm(IsSpaceQuery(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> StrForm:
        """Center string in field of given width."""
        from .str_interactions import CenterQuery

        return StrForm(CenterQuery(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> StrForm:
        """Left-justify string in field of given width."""
        from .str_interactions import LJustQuery

        return StrForm(LJustQuery(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> StrForm:
        """Right-justify string in field of given width."""
        from .str_interactions import RJustQuery

        return StrForm(RJustQuery(self, width, fillchar))

    def zfill(self, width: IntArg) -> StrForm:
        """Zero-fill string to given width."""
        from .str_interactions import ZFillQuery

        return StrForm(ZFillQuery(self, width))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> StrForm:
        """Replace occurrences of old with new."""
        from .str_interactions import ReplaceQuery

        return StrForm(ReplaceQuery(self, old, new, count))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> BytesForm:
        """Encode string to bytes."""
        from .bytes_ import BytesForm
        from .str_interactions import EncodeQuery

        return BytesForm(EncodeQuery(self, encoding))

    # =========================================================================
    # JOINING
    # =========================================================================

    def join(self, iterable: object) -> StrForm:
        """Join iterable elements with this string as separator."""
        from .str_interactions import JoinQuery

        return StrForm(JoinQuery(self, iterable))
