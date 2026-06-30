"""BytesForm - bytes interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.lang import BoolArg, BytesArg, IntArg, StrArg

    from ..collections.list_ import ListForm
    from ..collections.tuple_ import TupleForm
    from .bool_ import BoolForm
    from .int_ import IntForm
    from .str_ import StrForm


__all__ = [
    "BytesForm",
]


class BytesForm(Form, TypedNu[bytes]):
    """Bytes interface. Sliceable + comparable + logical + bytes methods."""

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: BytesArg) -> BytesForm:
        from nu.core import AddQuery

        return BytesForm(AddQuery(self, other))

    def __radd__(self, other: BytesArg) -> BytesForm:
        from nu.core import AddQuery

        return BytesForm(AddQuery(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> IntForm: ...
    @overload
    def __getitem__(self, key: slice) -> BytesForm: ...
    def __getitem__(self, key: IntArg | slice) -> BytesForm | IntForm:
        from nu.core import GetItemQuery, SliceQuery

        from .int_ import IntForm

        if isinstance(key, slice):
            return BytesForm(GetItemQuery(self, SliceQuery(key.start, key.stop, key.step)))
        return IntForm(GetItemQuery(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BytesArg) -> BoolForm:
        from nu.core import GtQuery

        from .bool_ import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: BytesArg) -> BoolForm:
        from nu.core import LtQuery

        from .bool_ import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: BytesArg) -> BoolForm:
        from nu.core import GeQuery

        from .bool_ import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: BytesArg) -> BoolForm:
        from nu.core import LeQuery

        from .bool_ import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: BytesArg) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from .bool_ import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: BytesArg) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from .bool_ import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: BytesArg) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from .bool_ import BoolForm

        return BoolForm(IsQuery(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BytesArg) -> BoolForm:
        """Logical AND: self AND other."""
        from nu.core import AndQuery

        from .bool_ import BoolForm

        return BoolForm(AndQuery(self, other))

    def or_(self, other: BytesArg) -> BoolForm:
        """Logical OR: self OR other."""
        from nu.core import OrQuery

        from .bool_ import BoolForm

        return BoolForm(OrQuery(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu.core import NotQuery

        from .bool_ import BoolForm

        return BoolForm(NotQuery(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu.core import BoolQuery

        from .bool_ import BoolForm

        return BoolForm(BoolQuery(self))

    # =========================================================================
    # BYTES METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> StrForm:
        """Decode bytes to string using the given encoding."""
        from .bytes_interactions import DecodeQuery
        from .str_ import StrForm

        return StrForm(DecodeQuery(self, encoding))

    def hex_(self) -> StrForm:
        """Convert bytes to hex string."""
        from .bytes_interactions import HexQuery
        from .str_ import StrForm

        return StrForm(HexQuery(self))

    def upper(self) -> BytesForm:
        """Convert bytes to uppercase."""
        from .bytes_interactions import BytesUpperQuery

        return BytesForm(BytesUpperQuery(self))

    def lower(self) -> BytesForm:
        """Convert bytes to lowercase."""
        from .bytes_interactions import BytesLowerQuery

        return BytesForm(BytesLowerQuery(self))

    def strip(self, chars: BytesArg | None = None) -> BytesForm:
        """Strip leading and trailing bytes."""
        from .bytes_interactions import BytesStripQuery

        return BytesForm(BytesStripQuery(self, chars))

    def lstrip(self, chars: BytesArg | None = None) -> BytesForm:
        """Strip leading bytes."""
        from .bytes_interactions import BytesLStripQuery

        return BytesForm(BytesLStripQuery(self, chars))

    def rstrip(self, chars: BytesArg | None = None) -> BytesForm:
        """Strip trailing bytes."""
        from .bytes_interactions import BytesRStripQuery

        return BytesForm(BytesRStripQuery(self, chars))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListForm:
        """Split bytes on sep, up to maxsplit times."""
        from ..collections.list_ import ListForm
        from .bytes_interactions import BytesSplitQuery

        if sep is not None:
            return ListForm(BytesSplitQuery(self, sep, maxsplit))
        return ListForm(BytesSplitQuery(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        """Find sub-bytes, returning the index or -1."""
        from .bytes_interactions import BytesFindQuery
        from .int_ import IntForm

        return IntForm(BytesFindQuery(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> IntForm:
        """Count non-overlapping occurrences of sub in bytes."""
        from .bytes_interactions import BytesCountQuery
        from .int_ import IntForm

        return IntForm(BytesCountQuery(self, sub))

    def startswith(self, prefix: BytesArg) -> BoolForm:
        """Return True if bytes start with prefix."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesStartsWithQuery

        return BoolForm(BytesStartsWithQuery(self, prefix))

    def endswith(self, suffix: BytesArg) -> BoolForm:
        """Return True if bytes end with suffix."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesEndsWithQuery

        return BoolForm(BytesEndsWithQuery(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> BytesForm:
        """Replace occurrences of old with new in bytes."""
        from .bytes_interactions import BytesReplaceQuery

        return BytesForm(BytesReplaceQuery(self, old, new, count))

    def removeprefix(self, prefix: BytesArg) -> BytesForm:
        """Remove prefix if present, else return bytes unchanged."""
        from .bytes_interactions import BytesRemovePrefixQuery

        return BytesForm(BytesRemovePrefixQuery(self, prefix))

    def removesuffix(self, suffix: BytesArg) -> BytesForm:
        """Remove suffix if present, else return bytes unchanged."""
        from .bytes_interactions import BytesRemoveSuffixQuery

        return BytesForm(BytesRemoveSuffixQuery(self, suffix))

    def translate(self, table: BytesArg | None, delete: BytesArg = b"") -> BytesForm:
        """Translate via a 256-length table, deleting bytes in delete."""
        from .bytes_interactions import BytesTranslateQuery

        return BytesForm(BytesTranslateQuery(self, table, delete))

    # =========================================================================
    # CASE TRANSFORMATION (extra)
    # =========================================================================

    def title(self) -> BytesForm:
        """Titlecase bytes."""
        from .bytes_interactions import BytesTitleQuery

        return BytesForm(BytesTitleQuery(self))

    def capitalize(self) -> BytesForm:
        """Capitalize bytes."""
        from .bytes_interactions import BytesCapitalizeQuery

        return BytesForm(BytesCapitalizeQuery(self))

    def swapcase(self) -> BytesForm:
        """Swap case of bytes."""
        from .bytes_interactions import BytesSwapCaseQuery

        return BytesForm(BytesSwapCaseQuery(self))

    # =========================================================================
    # SPLITTING (extra)
    # =========================================================================

    def rsplit_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListForm:
        """Split bytes from the right on sep, up to maxsplit times."""
        from ..collections.list_ import ListForm
        from .bytes_interactions import BytesRSplitQuery

        if sep is not None:
            return ListForm(BytesRSplitQuery(self, sep, maxsplit))
        return ListForm(BytesRSplitQuery(self, None, maxsplit))

    def splitlines(self, keepends: BoolArg = False) -> ListForm:
        """Split bytes on line boundaries."""
        from ..collections.list_ import ListForm
        from .bytes_interactions import BytesSplitLinesQuery

        return ListForm(BytesSplitLinesQuery(self, keepends))

    def partition(self, sep: BytesArg) -> TupleForm:
        """Partition on first occurrence of sep into a 3-tuple."""
        from ..collections.tuple_ import TupleForm
        from .bytes_interactions import BytesPartitionQuery

        return TupleForm(BytesPartitionQuery(self, sep))

    def rpartition(self, sep: BytesArg) -> TupleForm:
        """Partition on last occurrence of sep into a 3-tuple."""
        from ..collections.tuple_ import TupleForm
        from .bytes_interactions import BytesRPartitionQuery

        return TupleForm(BytesRPartitionQuery(self, sep))

    # =========================================================================
    # SEARCHING (extra)
    # =========================================================================

    def rfind_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        """Find sub-bytes from the right, returning the index or -1."""
        from .bytes_interactions import BytesRFindQuery
        from .int_ import IntForm

        return IntForm(BytesRFindQuery(self, sub, start, end))

    def index_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        """Find sub-bytes index, raising ValueError if absent."""
        from .bytes_interactions import BytesIndexQuery
        from .int_ import IntForm

        return IntForm(BytesIndexQuery(self, sub, start, end))

    def rindex_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        """Find sub-bytes index from the right, raising ValueError if absent."""
        from .bytes_interactions import BytesRIndexQuery
        from .int_ import IntForm

        return IntForm(BytesRIndexQuery(self, sub, start, end))

    # =========================================================================
    # PREDICATES
    # =========================================================================

    def isascii(self) -> BoolForm:
        """Return True if all bytes are ASCII (or empty)."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesIsAsciiQuery

        return BoolForm(BytesIsAsciiQuery(self))

    def isdigit(self) -> BoolForm:
        """Return True if all bytes are ASCII digits and there is at least one."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesIsDigitQuery

        return BoolForm(BytesIsDigitQuery(self))

    def isalpha(self) -> BoolForm:
        """Return True if all bytes are ASCII letters and there is at least one."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesIsAlphaQuery

        return BoolForm(BytesIsAlphaQuery(self))

    def isalnum(self) -> BoolForm:
        """Return True if all bytes are ASCII alphanumeric and there is at least one."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesIsAlnumQuery

        return BoolForm(BytesIsAlnumQuery(self))

    def isspace(self) -> BoolForm:
        """Return True if all bytes are ASCII whitespace and there is at least one."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesIsSpaceQuery

        return BoolForm(BytesIsSpaceQuery(self))

    def istitle(self) -> BoolForm:
        """Return True if bytes are titlecased and there is at least one cased byte."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesIsTitleQuery

        return BoolForm(BytesIsTitleQuery(self))

    def isupper(self) -> BoolForm:
        """Return True if all cased bytes are uppercase and there is at least one."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesIsUpperQuery

        return BoolForm(BytesIsUpperQuery(self))

    def islower(self) -> BoolForm:
        """Return True if all cased bytes are lowercase and there is at least one."""
        from .bool_ import BoolForm
        from .bytes_interactions import BytesIsLowerQuery

        return BoolForm(BytesIsLowerQuery(self))

    # =========================================================================
    # JUSTIFYING
    # =========================================================================

    def center(self, width: IntArg, fillbyte: BytesArg = b" ") -> BytesForm:
        """Center bytes in field of given width."""
        from .bytes_interactions import BytesCenterQuery

        return BytesForm(BytesCenterQuery(self, width, fillbyte))

    def ljust(self, width: IntArg, fillbyte: BytesArg = b" ") -> BytesForm:
        """Left-justify bytes in field of given width."""
        from .bytes_interactions import BytesLJustQuery

        return BytesForm(BytesLJustQuery(self, width, fillbyte))

    def rjust(self, width: IntArg, fillbyte: BytesArg = b" ") -> BytesForm:
        """Right-justify bytes in field of given width."""
        from .bytes_interactions import BytesRJustQuery

        return BytesForm(BytesRJustQuery(self, width, fillbyte))

    def zfill(self, width: IntArg) -> BytesForm:
        """Zero-fill bytes to given width."""
        from .bytes_interactions import BytesZFillQuery

        return BytesForm(BytesZFillQuery(self, width))

    # =========================================================================
    # TABS
    # =========================================================================

    def expandtabs(self, tabsize: IntArg = 8) -> BytesForm:
        """Expand tabs to spaces using the given tab size."""
        from .bytes_interactions import BytesExpandTabsQuery

        return BytesForm(BytesExpandTabsQuery(self, tabsize))

    # =========================================================================
    # JOINING
    # =========================================================================

    def join(self, iterable: Iterable[BytesArg]) -> BytesForm:
        """Join an iterable of bytes with this bytes as separator."""
        from .bytes_interactions import BytesJoinQuery

        return BytesForm(BytesJoinQuery(self, iterable))
