"""Bytes - bytes interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.lang import BoolArg, BytesArg, IntArg, StrArg

    from ..collections.list_ import List
    from ..collections.tuple_ import Tuple
    from .bool_ import Bool
    from .int_ import Int
    from .str_ import Str


__all__ = [
    "Bytes",
]


class Bytes(Form, TypedNu[bytes]):
    """Bytes interface. Sliceable + comparable + logical + bytes methods."""

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: BytesArg) -> Bytes:
        from nu.core import Add

        return Bytes(Add(self, other))

    def __radd__(self, other: BytesArg) -> Bytes:
        from nu.core import Add

        return Bytes(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> Int: ...
    @overload
    def __getitem__(self, key: slice) -> Bytes: ...
    def __getitem__(self, key: IntArg | slice) -> Bytes | Int:
        from nu.core import GetItem, Slice

        from .int_ import Int

        if isinstance(key, slice):
            return Bytes(GetItem(self, Slice(key.start, key.stop, key.step)))
        return Int(GetItem(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BytesArg) -> Bool:
        from nu.core import Gt

        from .bool_ import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: BytesArg) -> Bool:
        from nu.core import Lt

        from .bool_ import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: BytesArg) -> Bool:
        from nu.core import Ge

        from .bool_ import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: BytesArg) -> Bool:
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: BytesArg) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: BytesArg) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))

    def is_(self, other: BytesArg) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BytesArg) -> Bool:
        """Logical AND: self AND other."""
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: BytesArg) -> Bool:
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
    # BYTES METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> Str:
        """Decode bytes to string using the given encoding."""
        from .bytes_interactions import Decode
        from .str_ import Str

        return Str(Decode(self, encoding))

    def hex_(self) -> Str:
        """Convert bytes to hex string."""
        from .bytes_interactions import Hex
        from .str_ import Str

        return Str(Hex(self))

    def upper(self) -> Bytes:
        """Convert bytes to uppercase."""
        from .bytes_interactions import BytesUpper

        return Bytes(BytesUpper(self))

    def lower(self) -> Bytes:
        """Convert bytes to lowercase."""
        from .bytes_interactions import BytesLower

        return Bytes(BytesLower(self))

    def strip(self, chars: BytesArg | None = None) -> Bytes:
        """Strip leading and trailing bytes."""
        from .bytes_interactions import BytesStrip

        return Bytes(BytesStrip(self, chars))

    def lstrip(self, chars: BytesArg | None = None) -> Bytes:
        """Strip leading bytes."""
        from .bytes_interactions import BytesLStrip

        return Bytes(BytesLStrip(self, chars))

    def rstrip(self, chars: BytesArg | None = None) -> Bytes:
        """Strip trailing bytes."""
        from .bytes_interactions import BytesRStrip

        return Bytes(BytesRStrip(self, chars))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> List:
        """Split bytes on sep, up to maxsplit times."""
        from ..collections.list_ import List
        from .bytes_interactions import BytesSplit

        if sep is not None:
            return List(BytesSplit(self, sep, maxsplit))
        return List(BytesSplit(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Find sub-bytes, returning the index or -1."""
        from .bytes_interactions import BytesFind
        from .int_ import Int

        return Int(BytesFind(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> Int:
        """Count non-overlapping occurrences of sub in bytes."""
        from .bytes_interactions import BytesCount
        from .int_ import Int

        return Int(BytesCount(self, sub))

    def startswith(self, prefix: BytesArg) -> Bool:
        """Return True if bytes start with prefix."""
        from .bool_ import Bool
        from .bytes_interactions import BytesStartsWith

        return Bool(BytesStartsWith(self, prefix))

    def endswith(self, suffix: BytesArg) -> Bool:
        """Return True if bytes end with suffix."""
        from .bool_ import Bool
        from .bytes_interactions import BytesEndsWith

        return Bool(BytesEndsWith(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> Bytes:
        """Replace occurrences of old with new in bytes."""
        from .bytes_interactions import BytesReplace

        return Bytes(BytesReplace(self, old, new, count))

    def removeprefix(self, prefix: BytesArg) -> Bytes:
        """Remove prefix if present, else return bytes unchanged."""
        from .bytes_interactions import BytesRemovePrefix

        return Bytes(BytesRemovePrefix(self, prefix))

    def removesuffix(self, suffix: BytesArg) -> Bytes:
        """Remove suffix if present, else return bytes unchanged."""
        from .bytes_interactions import BytesRemoveSuffix

        return Bytes(BytesRemoveSuffix(self, suffix))

    def translate(self, table: BytesArg | None, delete: BytesArg = b"") -> Bytes:
        """Translate via a 256-length table, deleting bytes in delete."""
        from .bytes_interactions import BytesTranslate

        return Bytes(BytesTranslate(self, table, delete))

    # =========================================================================
    # CASE TRANSFORMATION (extra)
    # =========================================================================

    def title(self) -> Bytes:
        """Titlecase bytes."""
        from .bytes_interactions import BytesTitle

        return Bytes(BytesTitle(self))

    def capitalize(self) -> Bytes:
        """Capitalize bytes."""
        from .bytes_interactions import BytesCapitalize

        return Bytes(BytesCapitalize(self))

    def swapcase(self) -> Bytes:
        """Swap case of bytes."""
        from .bytes_interactions import BytesSwapCase

        return Bytes(BytesSwapCase(self))

    # =========================================================================
    # SPLITTING (extra)
    # =========================================================================

    def rsplit_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> List:
        """Split bytes from the right on sep, up to maxsplit times."""
        from ..collections.list_ import List
        from .bytes_interactions import BytesRSplit

        if sep is not None:
            return List(BytesRSplit(self, sep, maxsplit))
        return List(BytesRSplit(self, None, maxsplit))

    def splitlines(self, keepends: BoolArg = False) -> List:
        """Split bytes on line boundaries."""
        from ..collections.list_ import List
        from .bytes_interactions import BytesSplitLines

        return List(BytesSplitLines(self, keepends))

    def partition(self, sep: BytesArg) -> Tuple:
        """Partition on first occurrence of sep into a 3-tuple."""
        from ..collections.tuple_ import Tuple
        from .bytes_interactions import BytesPartition

        return Tuple(BytesPartition(self, sep))

    def rpartition(self, sep: BytesArg) -> Tuple:
        """Partition on last occurrence of sep into a 3-tuple."""
        from ..collections.tuple_ import Tuple
        from .bytes_interactions import BytesRPartition

        return Tuple(BytesRPartition(self, sep))

    # =========================================================================
    # SEARCHING (extra)
    # =========================================================================

    def rfind_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Find sub-bytes from the right, returning the index or -1."""
        from .bytes_interactions import BytesRFind
        from .int_ import Int

        return Int(BytesRFind(self, sub, start, end))

    def index_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Find sub-bytes index, raising ValueError if absent."""
        from .bytes_interactions import BytesIndex
        from .int_ import Int

        return Int(BytesIndex(self, sub, start, end))

    def rindex_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Find sub-bytes index from the right, raising ValueError if absent."""
        from .bytes_interactions import BytesRIndex
        from .int_ import Int

        return Int(BytesRIndex(self, sub, start, end))

    # =========================================================================
    # PREDICATES
    # =========================================================================

    def isascii(self) -> Bool:
        """Return True if all bytes are ASCII (or empty)."""
        from .bool_ import Bool
        from .bytes_interactions import BytesIsAscii

        return Bool(BytesIsAscii(self))

    def isdigit(self) -> Bool:
        """Return True if all bytes are ASCII digits and there is at least one."""
        from .bool_ import Bool
        from .bytes_interactions import BytesIsDigit

        return Bool(BytesIsDigit(self))

    def isalpha(self) -> Bool:
        """Return True if all bytes are ASCII letters and there is at least one."""
        from .bool_ import Bool
        from .bytes_interactions import BytesIsAlpha

        return Bool(BytesIsAlpha(self))

    def isalnum(self) -> Bool:
        """Return True if all bytes are ASCII alphanumeric and there is at least one."""
        from .bool_ import Bool
        from .bytes_interactions import BytesIsAlnum

        return Bool(BytesIsAlnum(self))

    def isspace(self) -> Bool:
        """Return True if all bytes are ASCII whitespace and there is at least one."""
        from .bool_ import Bool
        from .bytes_interactions import BytesIsSpace

        return Bool(BytesIsSpace(self))

    def istitle(self) -> Bool:
        """Return True if bytes are titlecased and there is at least one cased byte."""
        from .bool_ import Bool
        from .bytes_interactions import BytesIsTitle

        return Bool(BytesIsTitle(self))

    def isupper(self) -> Bool:
        """Return True if all cased bytes are uppercase and there is at least one."""
        from .bool_ import Bool
        from .bytes_interactions import BytesIsUpper

        return Bool(BytesIsUpper(self))

    def islower(self) -> Bool:
        """Return True if all cased bytes are lowercase and there is at least one."""
        from .bool_ import Bool
        from .bytes_interactions import BytesIsLower

        return Bool(BytesIsLower(self))

    # =========================================================================
    # JUSTIFYING
    # =========================================================================

    def center(self, width: IntArg, fillbyte: BytesArg = b" ") -> Bytes:
        """Center bytes in field of given width."""
        from .bytes_interactions import BytesCenter

        return Bytes(BytesCenter(self, width, fillbyte))

    def ljust(self, width: IntArg, fillbyte: BytesArg = b" ") -> Bytes:
        """Left-justify bytes in field of given width."""
        from .bytes_interactions import BytesLJust

        return Bytes(BytesLJust(self, width, fillbyte))

    def rjust(self, width: IntArg, fillbyte: BytesArg = b" ") -> Bytes:
        """Right-justify bytes in field of given width."""
        from .bytes_interactions import BytesRJust

        return Bytes(BytesRJust(self, width, fillbyte))

    def zfill(self, width: IntArg) -> Bytes:
        """Zero-fill bytes to given width."""
        from .bytes_interactions import BytesZFill

        return Bytes(BytesZFill(self, width))

    # =========================================================================
    # TABS
    # =========================================================================

    def expandtabs(self, tabsize: IntArg = 8) -> Bytes:
        """Expand tabs to spaces using the given tab size."""
        from .bytes_interactions import BytesExpandTabs

        return Bytes(BytesExpandTabs(self, tabsize))

    # =========================================================================
    # JOINING
    # =========================================================================

    def join(self, iterable: Iterable[BytesArg]) -> Bytes:
        """Join an iterable of bytes with this bytes as separator."""
        from .bytes_interactions import BytesJoin

        return Bytes(BytesJoin(self, iterable))
