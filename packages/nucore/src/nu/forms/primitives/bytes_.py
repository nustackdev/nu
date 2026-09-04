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
    """Bytes interface. Sliceable + comparable + logical + bytes methods.

    Notes:
        - Indexing with `[]` yields Int, the byte's value 0-255. Slicing
          with `[:]` yields Bytes.
        - `decode` and `hex_` are the only two methods that leave bytes:
          `decode` produces a Str, `hex_` produces a Str of hex digits.
          Every other method stays in Bytes.
        - Comparison operators yield Bool, ordering lexicographically by
          byte value, same as Python's `bytes` ordering.
        - Logical operators are the named forms `and_`, `or_`, `not_`.

    Example:
        >>> nu.run(nu.Bytes(b"hi") + nu.Bytes(b" there"))[0]
        b'hi there'
    """

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: BytesArg) -> Bytes:
        """Concatenation of self and other.

        Args:
            other: the bytes to append to self.

        Yields:
            The concatenation. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"foo") + nu.Bytes(b"bar"))[0]
            b'foobar'
        """
        from nu.core import Add

        return Bytes(Add(self, other))

    def __radd__(self, other: BytesArg) -> Bytes:
        """Concatenation of other and self, with self on the right.

        Args:
            other: the bytes on the left of the `+`.

        Notes:
            - Reached only when the left operand is a plain Python bytes
              object. A Nu Bytes on the left goes through its own
              `__add__` first and never lands here.

        Yields:
            The concatenation. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(b"foo" + nu.Bytes(b"bar"))[0]
            b'foobar'
        """
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
        """Byte at an index, or a sub-range by slice.

        Args:
            key: an Int or plain int for a single byte, or a Python slice
                for a sub-range.

        Yields:
            The byte's value 0-255 as Int for a single index. A new Bytes
            for a slice. INVALID when self is a sentinel or the index is
            out of range.

        Example:
            >>> nu.run(nu.Bytes(b"hello")[1])[0]
            101

            >>> nu.run(nu.Bytes(b"hello")[1:3])[0]
            b'el'
        """
        from nu.core import GetItem, Slice

        from .int_ import Int

        if isinstance(key, slice):
            return Bytes(GetItem(self, Slice(key.start, key.stop, key.step)))
        return Int(GetItem(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BytesArg) -> Bool:
        """Self strictly greater than other.

        Args:
            other: the bytes to compare against.

        Yields:
            True when self sorts after other, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"b") > nu.Bytes(b"a"))[0]
            True
        """
        from nu.core import Gt

        from .bool_ import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: BytesArg) -> Bool:
        """Self strictly less than other.

        Args:
            other: the bytes to compare against.

        Yields:
            True when self sorts before other, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"a") < nu.Bytes(b"b"))[0]
            True
        """
        from nu.core import Lt

        from .bool_ import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: BytesArg) -> Bool:
        """Self greater than or equal to other.

        Args:
            other: the bytes to compare against.

        Yields:
            True when self sorts after or equal to other, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"a") >= nu.Bytes(b"a"))[0]
            True
        """
        from nu.core import Ge

        from .bool_ import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: BytesArg) -> Bool:
        """Self less than or equal to other.

        Args:
            other: the bytes to compare against.

        Yields:
            True when self sorts before or equal to other, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"a") <= nu.Bytes(b"b"))[0]
            True
        """
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: BytesArg) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the bytes to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the byte values are equal, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"abc") == nu.Bytes(b"abc"))[0]
            True
        """
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: BytesArg) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the bytes to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the byte values differ, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"abc") != nu.Bytes(b"xyz"))[0]
            True
        """
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))

    def is_(self, other: BytesArg) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For value comparison use
              `==` instead.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.Bytes(b"abc").is_(b"abc"))[0]
            True
        """
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BytesArg) -> Bool:
        """Logical AND of self and other.

        Args:
            other: the value to AND with self. Coerced to Bool by
                truthiness (empty bytes is False, everything else is True).

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.

        Yields:
            True when both operands are truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"").and_(nu.Bytes(b"x")))[0]
            False
        """
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: BytesArg) -> Bool:
        """Logical OR of self and other.

        Args:
            other: the value to OR with self. Coerced to Bool by
                truthiness.

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.

        Yields:
            True when either operand is truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"x").or_(nu.Bytes(b"")))[0]
            True
        """
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT of self.

        Notes:
            - Empty bytes yields True, every other value yields False.

        Yields:
            True when self is empty, False otherwise. INVALID when self is
            a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"").not_())[0]
            True
        """
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Cast self to Bool.

        Notes:
            - Empty bytes becomes False, every other value becomes True,
              matching Python's truthiness rule.

        Yields:
            True when self is non-empty, False when self is empty. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"hi").bool_())[0]
            True
        """
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # BYTES METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> Str:
        """Decode self to a string using the given encoding.

        Args:
            encoding: the codec to decode with, `"utf-8"` by default.

        Notes:
            - This is where Bytes crosses into Str. Every other method on
              this class stays in bytes.

        Yields:
            The decoded Str. INVALID when self is a sentinel, when the
            bytes are not valid under the encoding, or when the encoding
            name is unknown.

        Example:
            >>> nu.run(nu.Bytes(b"hi there").decode())[0]
            'hi there'
        """
        from .bytes_interactions import Decode
        from .str_ import Str

        return Str(Decode(self, encoding))

    def hex_(self) -> Str:
        r"""Hex string of self, two digits per byte.

        Notes:
            - The other place, besides `decode`, where Bytes crosses into
              Str.

        Yields:
            The lowercase hex digits, no separators. INVALID when self is a
            sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"\\xff\\x00").hex_())[0]
            'ff00'
        """
        from .bytes_interactions import Hex
        from .str_ import Str

        return Str(Hex(self))

    def upper(self) -> Bytes:
        """Self with ASCII letters uppercased.

        Notes:
            - ASCII only. Non-ASCII bytes pass through unchanged.

        Yields:
            The uppercased bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"Hi").upper())[0]
            b'HI'
        """
        from .bytes_interactions import BytesUpper

        return Bytes(BytesUpper(self))

    def lower(self) -> Bytes:
        """Self with ASCII letters lowercased.

        Notes:
            - ASCII only. Non-ASCII bytes pass through unchanged.

        Yields:
            The lowercased bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"Hi").lower())[0]
            b'hi'
        """
        from .bytes_interactions import BytesLower

        return Bytes(BytesLower(self))

    def strip(self, chars: BytesArg | None = None) -> Bytes:
        """Self with leading and trailing bytes removed.

        Args:
            chars: the bytes to strip. `None` strips ASCII whitespace.

        Yields:
            The stripped bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"  hi  ").strip())[0]
            b'hi'
        """
        from .bytes_interactions import BytesStrip

        return Bytes(BytesStrip(self, chars))

    def lstrip(self, chars: BytesArg | None = None) -> Bytes:
        """Self with leading bytes removed.

        Args:
            chars: the bytes to strip. `None` strips ASCII whitespace.

        Yields:
            The stripped bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"  hi  ").lstrip())[0]
            b'hi  '
        """
        from .bytes_interactions import BytesLStrip

        return Bytes(BytesLStrip(self, chars))

    def rstrip(self, chars: BytesArg | None = None) -> Bytes:
        """Self with trailing bytes removed.

        Args:
            chars: the bytes to strip. `None` strips ASCII whitespace.

        Yields:
            The stripped bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"  hi  ").rstrip())[0]
            b'  hi'
        """
        from .bytes_interactions import BytesRStrip

        return Bytes(BytesRStrip(self, chars))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> List:
        """Self split into a List of Bytes on sep.

        Args:
            sep: the separator. `None` splits on runs of ASCII whitespace
                and drops empty pieces.
            maxsplit: the maximum number of splits. `-1` means no limit.

        Yields:
            The pieces as a List of Bytes. INVALID when self is a
            sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"a,b,c").split_bytes(b","))[0]
            [b'a', b'b', b'c']
        """
        from ..collections.list_ import List
        from .bytes_interactions import BytesSplit

        if sep is not None:
            return List(BytesSplit(self, sep, maxsplit))
        return List(BytesSplit(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Lowest index of sub in self, or -1 if absent.

        Args:
            sub: the bytes to search for.
            start: the index to start searching from.
            end: the index to stop searching at, exclusive. `None` means
                the end of self.

        Yields:
            The index of the first match, or -1 when sub is not found.
            INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"abcabc").find_bytes(b"bc"))[0]
            1
        """
        from .bytes_interactions import BytesFind
        from .int_ import Int

        return Int(BytesFind(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> Int:
        """Number of non-overlapping occurrences of sub in self.

        Args:
            sub: the bytes to count.

        Yields:
            The count. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"abcabc").count_bytes(b"bc"))[0]
            2
        """
        from .bytes_interactions import BytesCount
        from .int_ import Int

        return Int(BytesCount(self, sub))

    def startswith(self, prefix: BytesArg) -> Bool:
        """Self starts with prefix.

        Args:
            prefix: the bytes to test for.

        Yields:
            True when self starts with prefix, False otherwise. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"hello").startswith(b"he"))[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesStartsWith

        return Bool(BytesStartsWith(self, prefix))

    def endswith(self, suffix: BytesArg) -> Bool:
        """Self ends with suffix.

        Args:
            suffix: the bytes to test for.

        Yields:
            True when self ends with suffix, False otherwise. INVALID when
            self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"hello").endswith(b"lo"))[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesEndsWith

        return Bool(BytesEndsWith(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> Bytes:
        """Self with occurrences of old replaced by new.

        Args:
            old: the bytes to replace.
            new: the replacement bytes.
            count: the maximum number of replacements. `-1` replaces every
                occurrence.

        Yields:
            The replaced bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"aXbXc").replace(b"X", b"-"))[0]
            b'a-b-c'
        """
        from .bytes_interactions import BytesReplace

        return Bytes(BytesReplace(self, old, new, count))

    def removeprefix(self, prefix: BytesArg) -> Bytes:
        """Self with prefix removed if present.

        Args:
            prefix: the bytes to remove from the start.

        Yields:
            Self without the leading prefix, or self unchanged when the
            prefix is not present. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"prefoo").removeprefix(b"pre"))[0]
            b'foo'
        """
        from .bytes_interactions import BytesRemovePrefix

        return Bytes(BytesRemovePrefix(self, prefix))

    def removesuffix(self, suffix: BytesArg) -> Bytes:
        """Self with suffix removed if present.

        Args:
            suffix: the bytes to remove from the end.

        Yields:
            Self without the trailing suffix, or self unchanged when the
            suffix is not present. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"foobar").removesuffix(b"bar"))[0]
            b'foo'
        """
        from .bytes_interactions import BytesRemoveSuffix

        return Bytes(BytesRemoveSuffix(self, suffix))

    def translate(self, table: BytesArg | None, delete: BytesArg = b"") -> Bytes:
        """Self translated through a 256-byte table, with bytes in delete dropped first.

        Args:
            table: a 256-byte lookup table mapping each byte value to its
                replacement. `None` skips translation and only applies
                delete.
            delete: bytes to drop from self before translating.

        Yields:
            The translated bytes. INVALID when self is a sentinel, or when
            table is not exactly 256 bytes long.

        Example:
            >>> nu.run(nu.Bytes(b"abc").translate(bytes.maketrans(b"ab", b"AB")))[0]
            b'ABc'
        """
        from .bytes_interactions import BytesTranslate

        return Bytes(BytesTranslate(self, table, delete))

    # =========================================================================
    # CASE TRANSFORMATION (extra)
    # =========================================================================

    def title(self) -> Bytes:
        """Self titlecased: each word's first cased byte upper, the rest lower.

        Yields:
            The titlecased bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"hello world").title())[0]
            b'Hello World'
        """
        from .bytes_interactions import BytesTitle

        return Bytes(BytesTitle(self))

    def capitalize(self) -> Bytes:
        """Self with the first byte uppercased and the rest lowercased.

        Yields:
            The capitalized bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"hello world").capitalize())[0]
            b'Hello world'
        """
        from .bytes_interactions import BytesCapitalize

        return Bytes(BytesCapitalize(self))

    def swapcase(self) -> Bytes:
        """Self with uppercase and lowercase bytes swapped.

        Yields:
            The case-swapped bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"Hello").swapcase())[0]
            b'hELLO'
        """
        from .bytes_interactions import BytesSwapCase

        return Bytes(BytesSwapCase(self))

    # =========================================================================
    # SPLITTING (extra)
    # =========================================================================

    def rsplit_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> List:
        """Self split into a List of Bytes on sep, counting maxsplit from the right.

        Args:
            sep: the separator. `None` splits on runs of ASCII whitespace
                and drops empty pieces.
            maxsplit: the maximum number of splits, applied from the right.
                `-1` means no limit.

        Notes:
            - Only differs from `split_bytes` when maxsplit limits the
              split count; the pieces themselves are the same bytes either
              way.

        Yields:
            The pieces as a List of Bytes. INVALID when self is a
            sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"a,b,c").rsplit_bytes(b",", 1))[0]
            [b'a,b', b'c']
        """
        from ..collections.list_ import List
        from .bytes_interactions import BytesRSplit

        if sep is not None:
            return List(BytesRSplit(self, sep, maxsplit))
        return List(BytesRSplit(self, None, maxsplit))

    def splitlines(self, keepends: BoolArg = False) -> List:
        r"""Self split into a List of Bytes at line boundaries.

        Args:
            keepends: when True, keep the line-ending bytes on each piece.

        Yields:
            The lines as a List of Bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"a\\nb\\nc").splitlines())[0]
            [b'a', b'b', b'c']
        """
        from ..collections.list_ import List
        from .bytes_interactions import BytesSplitLines

        return List(BytesSplitLines(self, keepends))

    def partition(self, sep: BytesArg) -> Tuple:
        """Self split around the first occurrence of sep.

        Args:
            sep: the separator to split on.

        Yields:
            A 3-tuple of (before, sep, after). When sep is not found,
            (self, b"", b""). INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"key=value").partition(b"="))[0]
            (b'key', b'=', b'value')
        """
        from ..collections.tuple_ import Tuple
        from .bytes_interactions import BytesPartition

        return Tuple(BytesPartition(self, sep))

    def rpartition(self, sep: BytesArg) -> Tuple:
        """Self split around the last occurrence of sep.

        Args:
            sep: the separator to split on.

        Yields:
            A 3-tuple of (before, sep, after). When sep is not found,
            (b"", b"", self). INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"a=b=c").rpartition(b"="))[0]
            (b'a=b', b'=', b'c')
        """
        from ..collections.tuple_ import Tuple
        from .bytes_interactions import BytesRPartition

        return Tuple(BytesRPartition(self, sep))

    # =========================================================================
    # SEARCHING (extra)
    # =========================================================================

    def rfind_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Highest index of sub in self, or -1 if absent.

        Args:
            sub: the bytes to search for.
            start: the index to start searching from.
            end: the index to stop searching at, exclusive. `None` means
                the end of self.

        Yields:
            The index of the last match, or -1 when sub is not found.
            INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"abcabc").rfind_bytes(b"bc"))[0]
            4
        """
        from .bytes_interactions import BytesRFind
        from .int_ import Int

        return Int(BytesRFind(self, sub, start, end))

    def index_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Lowest index of sub in self.

        Args:
            sub: the bytes to search for.
            start: the index to start searching from.
            end: the index to stop searching at, exclusive. `None` means
                the end of self.

        Notes:
            - Like `find_bytes` but INVALID instead of -1 when sub is not
              found, mirroring Python's `index` raising `ValueError`.

        Yields:
            The index of the first match. INVALID when self is a sentinel
            or when sub is not found.

        Example:
            >>> nu.run(nu.Bytes(b"abc").index_bytes(b"b"))[0]
            1
        """
        from .bytes_interactions import BytesIndex
        from .int_ import Int

        return Int(BytesIndex(self, sub, start, end))

    def rindex_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Highest index of sub in self.

        Args:
            sub: the bytes to search for.
            start: the index to start searching from.
            end: the index to stop searching at, exclusive. `None` means
                the end of self.

        Notes:
            - Like `rfind_bytes` but INVALID instead of -1 when sub is not
              found, mirroring Python's `rindex` raising `ValueError`.

        Yields:
            The index of the last match. INVALID when self is a sentinel
            or when sub is not found.

        Example:
            >>> nu.run(nu.Bytes(b"abcabc").rindex_bytes(b"bc"))[0]
            4
        """
        from .bytes_interactions import BytesRIndex
        from .int_ import Int

        return Int(BytesRIndex(self, sub, start, end))

    # =========================================================================
    # PREDICATES
    # =========================================================================

    def isascii(self) -> Bool:
        """Self has only ASCII bytes.

        Notes:
            - Empty bytes is True.

        Yields:
            True when every byte is ASCII, False otherwise. INVALID when
            self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"hello").isascii())[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesIsAscii

        return Bool(BytesIsAscii(self))

    def isdigit(self) -> Bool:
        """Self has only ASCII digit bytes, and at least one.

        Yields:
            True when every byte is an ASCII digit and self is non-empty,
            False otherwise. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"123").isdigit())[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesIsDigit

        return Bool(BytesIsDigit(self))

    def isalpha(self) -> Bool:
        """Self has only ASCII letter bytes, and at least one.

        Yields:
            True when every byte is an ASCII letter and self is non-empty,
            False otherwise. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"abc").isalpha())[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesIsAlpha

        return Bool(BytesIsAlpha(self))

    def isalnum(self) -> Bool:
        """Self has only ASCII alphanumeric bytes, and at least one.

        Yields:
            True when every byte is an ASCII letter or digit and self is
            non-empty, False otherwise. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"abc123").isalnum())[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesIsAlnum

        return Bool(BytesIsAlnum(self))

    def isspace(self) -> Bool:
        """Self has only ASCII whitespace bytes, and at least one.

        Yields:
            True when every byte is ASCII whitespace and self is non-empty,
            False otherwise. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"  ").isspace())[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesIsSpace

        return Bool(BytesIsSpace(self))

    def istitle(self) -> Bool:
        """Self is titlecased, with at least one cased byte.

        Yields:
            True when self follows title case, False otherwise. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"Hello World").istitle())[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesIsTitle

        return Bool(BytesIsTitle(self))

    def isupper(self) -> Bool:
        """Self has all cased bytes uppercase, and at least one cased byte.

        Yields:
            True when every cased byte is uppercase, False otherwise.
            INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"ABC").isupper())[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesIsUpper

        return Bool(BytesIsUpper(self))

    def islower(self) -> Bool:
        """Self has all cased bytes lowercase, and at least one cased byte.

        Yields:
            True when every cased byte is lowercase, False otherwise.
            INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"abc").islower())[0]
            True
        """
        from .bool_ import Bool
        from .bytes_interactions import BytesIsLower

        return Bool(BytesIsLower(self))

    # =========================================================================
    # JUSTIFYING
    # =========================================================================

    def center(self, width: IntArg, fillbyte: BytesArg = b" ") -> Bytes:
        """Self centered in a field of width, padded with fillbyte.

        Args:
            width: the target length. Self unchanged when width does not
                exceed its length.
            fillbyte: the single byte to pad with, `b" "` by default.

        Yields:
            The padded bytes. INVALID when self is a sentinel, or when
            fillbyte is not exactly one byte.

        Example:
            >>> nu.run(nu.Bytes(b"hi").center(6))[0]
            b'  hi  '
        """
        from .bytes_interactions import BytesCenter

        return Bytes(BytesCenter(self, width, fillbyte))

    def ljust(self, width: IntArg, fillbyte: BytesArg = b" ") -> Bytes:
        """Self left-justified in a field of width, padded with fillbyte.

        Args:
            width: the target length. Self unchanged when width does not
                exceed its length.
            fillbyte: the single byte to pad with, `b" "` by default.

        Yields:
            The padded bytes. INVALID when self is a sentinel, or when
            fillbyte is not exactly one byte.

        Example:
            >>> nu.run(nu.Bytes(b"hi").ljust(5))[0]
            b'hi   '
        """
        from .bytes_interactions import BytesLJust

        return Bytes(BytesLJust(self, width, fillbyte))

    def rjust(self, width: IntArg, fillbyte: BytesArg = b" ") -> Bytes:
        """Self right-justified in a field of width, padded with fillbyte.

        Args:
            width: the target length. Self unchanged when width does not
                exceed its length.
            fillbyte: the single byte to pad with, `b" "` by default.

        Yields:
            The padded bytes. INVALID when self is a sentinel, or when
            fillbyte is not exactly one byte.

        Example:
            >>> nu.run(nu.Bytes(b"hi").rjust(5))[0]
            b'   hi'
        """
        from .bytes_interactions import BytesRJust

        return Bytes(BytesRJust(self, width, fillbyte))

    def zfill(self, width: IntArg) -> Bytes:
        """Self padded with leading zero bytes to width.

        Args:
            width: the target length. Self unchanged when width does not
                exceed its length.

        Notes:
            - A leading sign byte (`+` or `-`), if present, stays first and
              the zeros go after it.

        Yields:
            The zero-padded bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"42").zfill(5))[0]
            b'00042'
        """
        from .bytes_interactions import BytesZFill

        return Bytes(BytesZFill(self, width))

    # =========================================================================
    # TABS
    # =========================================================================

    def expandtabs(self, tabsize: IntArg = 8) -> Bytes:
        r"""Self with tab bytes expanded to spaces.

        Args:
            tabsize: the number of columns per tab stop, 8 by default.

        Yields:
            The expanded bytes. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Bytes(b"a\\tb").expandtabs(4))[0]
            b'a   b'
        """
        from .bytes_interactions import BytesExpandTabs

        return Bytes(BytesExpandTabs(self, tabsize))

    # =========================================================================
    # JOINING
    # =========================================================================

    def join(self, iterable: Iterable[BytesArg]) -> Bytes:
        """Self used as separator between the elements of iterable.

        Args:
            iterable: the bytes-like elements to join.

        Yields:
            The joined bytes. INVALID when self is a sentinel, or when any
            element is not bytes.

        Example:
            >>> nu.run(nu.Bytes(b",").join([b"a", b"b", b"c"]))[0]
            b'a,b,c'
        """
        from .bytes_interactions import BytesJoin

        return Bytes(BytesJoin(self, iterable))
