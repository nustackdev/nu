"""Str - string interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.lang import BoolArg, DictArg, IntArg, StrArg

    from ..collections.list_ import List
    from ..collections.tuple_ import Tuple
    from .bool_ import Bool
    from .bytes_ import Bytes
    from .int_ import Int


__all__ = [
    "Str",
]


class Str(Form, TypedNu[str]):
    """String interface. Addable + sliceable + comparable + logical + string methods."""

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: StrArg) -> Str:
        from nu.core import Add

        return Str(Add(self, other))

    def __radd__(self, other: StrArg) -> Str:
        from nu.core import Add

        return Str(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> Str: ...
    @overload
    def __getitem__(self, key: slice) -> Str: ...
    def __getitem__(self, key: IntArg | slice) -> Str:
        from nu.core import GetItem, Slice

        if isinstance(key, slice):
            return Str(GetItem(self, Slice(key.start, key.stop, key.step)))
        return Str(GetItem(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: StrArg) -> Bool:
        from nu.core import Gt

        from .bool_ import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: StrArg) -> Bool:
        from nu.core import Lt

        from .bool_ import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: StrArg) -> Bool:
        from nu.core import Ge

        from .bool_ import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: StrArg) -> Bool:
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: StrArg) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: StrArg) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))

    def is_(self, other: StrArg) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: StrArg) -> Bool:
        """Logical AND: self AND other."""
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: StrArg) -> Bool:
        """Logical OR: self OR other."""
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT: NOT self."""
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Convert to boolean."""
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> Str:
        """Convert to uppercase."""
        from .str_interactions import Upper

        return Str(Upper(self))

    def lower(self) -> Str:
        """Convert to lowercase."""
        from .str_interactions import Lower

        return Str(Lower(self))

    def title(self) -> Str:
        """Convert to title case."""
        from .str_interactions import Title

        return Str(Title(self))

    def capitalize(self) -> Str:
        """Capitalize first character."""
        from .str_interactions import Capitalize

        return Str(Capitalize(self))

    def swapcase(self) -> Str:
        """Swap case of all characters."""
        from .str_interactions import SwapCase

        return Str(SwapCase(self))

    def casefold(self) -> Str:
        """Casefold for caseless matching."""
        from .str_interactions import Casefold

        return Str(Casefold(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> Str:
        """Strip leading and trailing whitespace or chars."""
        from .str_interactions import Strip

        return Str(Strip(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> Str:
        """Strip leading whitespace or chars."""
        from .str_interactions import LStrip

        return Str(LStrip(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> Str:
        """Strip trailing whitespace or chars."""
        from .str_interactions import RStrip

        return Str(RStrip(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> List:
        """Split string into list on sep."""
        from ..collections.list_ import List
        from .str_interactions import Split

        return List(Split(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> List:
        """Right-split string into list on sep."""
        from ..collections.list_ import List
        from .str_interactions import RSplit

        return List(RSplit(self, sep, maxsplit))

    def splitlines(self, keepends: BoolArg = False) -> List:
        """Split at line boundaries into a list."""
        from ..collections.list_ import List
        from .str_interactions import SplitLines

        return List(SplitLines(self, keepends))

    def partition(self, sep: StrArg) -> Tuple:
        """Split around first occurrence of sep into a 3-tuple."""
        from ..collections.tuple_ import Tuple
        from .str_interactions import Partition

        return Tuple(Partition(self, sep))

    def rpartition(self, sep: StrArg) -> Tuple:
        """Split around last occurrence of sep into a 3-tuple."""
        from ..collections.tuple_ import Tuple
        from .str_interactions import RPartition

        return Tuple(RPartition(self, sep))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Find substring index: str.find(sub, start, end)."""
        from .int_ import Int
        from .str_interactions import Find

        return Int(Find(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Find substring index from right: str.rfind(sub, start, end)."""
        from .int_ import Int
        from .str_interactions import RFind

        return Int(RFind(self, sub, start, end))

    def index(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Find substring index, error if absent: str.index(sub, start, end)."""
        from .int_ import Int
        from .str_interactions import Index

        return Int(Index(self, sub, start, end))

    def rindex(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Find substring index from right, error if absent: str.rindex(sub, start, end)."""
        from .int_ import Int
        from .str_interactions import RIndex

        return Int(RIndex(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> Int:
        """Count non-overlapping occurrences of sub."""
        from .int_ import Int
        from .str_interactions import CountSubstring

        return Int(CountSubstring(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> Bool:
        """Check if string starts with prefix."""
        from .bool_ import Bool
        from .str_interactions import StartsWith

        return Bool(StartsWith(self, prefix))

    def endswith(self, suffix: StrArg) -> Bool:
        """Check if string ends with suffix."""
        from .bool_ import Bool
        from .str_interactions import EndsWith

        return Bool(EndsWith(self, suffix))

    def isdigit(self) -> Bool:
        """Check if all characters are digits."""
        from .bool_ import Bool
        from .str_interactions import IsDigit

        return Bool(IsDigit(self))

    def isalpha(self) -> Bool:
        """Check if all characters are alphabetic."""
        from .bool_ import Bool
        from .str_interactions import IsAlpha

        return Bool(IsAlpha(self))

    def isalnum(self) -> Bool:
        """Check if all characters are alphanumeric."""
        from .bool_ import Bool
        from .str_interactions import IsAlnum

        return Bool(IsAlnum(self))

    def isspace(self) -> Bool:
        """Check if all characters are whitespace."""
        from .bool_ import Bool
        from .str_interactions import IsSpace

        return Bool(IsSpace(self))

    def isnumeric(self) -> Bool:
        """Check if all characters are numeric."""
        from .bool_ import Bool
        from .str_interactions import IsNumeric

        return Bool(IsNumeric(self))

    def isdecimal(self) -> Bool:
        """Check if all characters are decimal."""
        from .bool_ import Bool
        from .str_interactions import IsDecimal

        return Bool(IsDecimal(self))

    def isidentifier(self) -> Bool:
        """Check if string is a valid identifier."""
        from .bool_ import Bool
        from .str_interactions import IsIdentifier

        return Bool(IsIdentifier(self))

    def isprintable(self) -> Bool:
        """Check if all characters are printable."""
        from .bool_ import Bool
        from .str_interactions import IsPrintable

        return Bool(IsPrintable(self))

    def istitle(self) -> Bool:
        """Check if string is titlecased."""
        from .bool_ import Bool
        from .str_interactions import IsTitle

        return Bool(IsTitle(self))

    def isupper(self) -> Bool:
        """Check if all cased characters are uppercase."""
        from .bool_ import Bool
        from .str_interactions import IsUpper

        return Bool(IsUpper(self))

    def islower(self) -> Bool:
        """Check if all cased characters are lowercase."""
        from .bool_ import Bool
        from .str_interactions import IsLower

        return Bool(IsLower(self))

    def isascii(self) -> Bool:
        """Check if all characters are ASCII (empty string is True)."""
        from .bool_ import Bool
        from .str_interactions import IsAscii

        return Bool(IsAscii(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> Str:
        """Center string in field of given width."""
        from .str_interactions import Center

        return Str(Center(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> Str:
        """Left-justify string in field of given width."""
        from .str_interactions import LJust

        return Str(LJust(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> Str:
        """Right-justify string in field of given width."""
        from .str_interactions import RJust

        return Str(RJust(self, width, fillchar))

    def zfill(self, width: IntArg) -> Str:
        """Zero-fill string to given width."""
        from .str_interactions import ZFill

        return Str(ZFill(self, width))

    def expandtabs(self, tabsize: IntArg = 8) -> Str:
        """Expand tabs to spaces using the given tab size."""
        from .str_interactions import ExpandTabs

        return Str(ExpandTabs(self, tabsize))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> Str:
        """Replace occurrences of old with new."""
        from .str_interactions import Replace

        return Str(Replace(self, old, new, count))

    def removeprefix(self, prefix: StrArg) -> Str:
        """Remove the given prefix if present."""
        from .str_interactions import RemovePrefix

        return Str(RemovePrefix(self, prefix))

    def removesuffix(self, suffix: StrArg) -> Str:
        """Remove the given suffix if present."""
        from .str_interactions import RemoveSuffix

        return Str(RemoveSuffix(self, suffix))

    def translate(self, table: DictArg) -> Str:
        """Map characters through a translation table."""
        from .str_interactions import Translate

        return Str(Translate(self, table))

    # =========================================================================
    # FORMATTING
    # =========================================================================

    def format_map(self, mapping: DictArg) -> Str:
        """Format the string using a mapping of field values."""
        from .str_interactions import FormatMap

        return Str(FormatMap(self, mapping))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> Bytes:
        """Encode string to bytes."""
        from .bytes_ import Bytes
        from .str_interactions import Encode

        return Bytes(Encode(self, encoding))

    # =========================================================================
    # JOINING
    # =========================================================================

    def join(self, iterable: object) -> Str:
        """Join iterable elements with this string as separator."""
        from .str_interactions import Join

        return Str(Join(self, iterable))
