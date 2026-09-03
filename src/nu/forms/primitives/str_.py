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
    """String interface. Addable + sliceable + comparable + logical + string methods.

    Notes:
        - `+` concatenates; there's no numeric arithmetic on Str.
        - Comparison operators compare lexicographically, Python str
          ordering, and yield Bool. Chained comparisons like `a > b > c`
          do not build a single term; write them as `And(a > b, b > c)`.
        - Logical operators are the named forms `and_`, `or_`, `not_`, and
          coerce by truthiness: the empty string is False, every other
          string is True.
        - Most string methods degrade to INVALID on failure rather than
          raising at evaluation time (a missing `index`/`rindex` match, a
          multi-character `fillchar`, an unencodable character, a missing
          `format_map` key). Indexing with an out-of-range int is the
          exception: it raises, matching Python.

    Example:
        >>> nu.run(nu.Str("ab") + nu.Str("cd"))[0]
        'abcd'
    """

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: StrArg) -> Str:
        """Concatenation of self and other.

        Args:
            other: the string to append to self.

        Yields:
            The concatenation. INVALID when either operand is not a Str or
            is a sentinel.

        Example:
            >>> nu.run(nu.Str("foo") + nu.Str("bar"))[0]
            'foobar'
        """
        from nu.core import Add

        return Str(Add(self, other))

    def __radd__(self, other: StrArg) -> Str:
        """Concatenation of other and self, with self on the right.

        Args:
            other: the string on the left of the `+`.

        Notes:
            - Reached only when the left operand is a plain Python str. A
              Nu Str on the left goes through its own `__add__` first and
              never lands here.

        Yields:
            The concatenation. INVALID when either operand is not a Str or
            is a sentinel.

        Example:
            >>> nu.run("foo" + nu.Str("bar"))[0]
            'foobar'
        """
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
        """Character at an int index, or substring for a slice.

        Args:
            key: an int index, or a Python slice of int start/stop/step.

        Notes:
            - An out-of-range int index raises at evaluation time, matching
              Python. A slice never raises; out-of-range bounds are clamped
              like Python slicing, so `s[10:20]` on a shorter string yields
              the empty string rather than erroring.
            - Negative indices and negative slice bounds work as in Python.

        Yields:
            The single character for an int key, the substring for a slice.
            INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("hello")[1])[0]
            'e'

            >>> nu.run(nu.Str("hello")[1:4])[0]
            'ell'
        """
        from nu.core import GetItem, Slice

        if isinstance(key, slice):
            return Str(GetItem(self, Slice(key.start, key.stop, key.step)))
        return Str(GetItem(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: StrArg) -> Bool:
        """Self strictly greater than other, lexicographically.

        Args:
            other: the string to compare against.

        Yields:
            True when self sorts after other, False otherwise. INVALID when
            either operand is not a Str or is a sentinel.

        Example:
            >>> nu.run(nu.Str("banana") > nu.Str("apple"))[0]
            True
        """
        from nu.core import Gt

        from .bool_ import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: StrArg) -> Bool:
        """Self strictly less than other, lexicographically.

        Args:
            other: the string to compare against.

        Yields:
            True when self sorts before other, False otherwise. INVALID
            when either operand is not a Str or is a sentinel.

        Example:
            >>> nu.run(nu.Str("apple") < nu.Str("banana"))[0]
            True
        """
        from nu.core import Lt

        from .bool_ import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: StrArg) -> Bool:
        """Self greater than or equal to other, lexicographically.

        Args:
            other: the string to compare against.

        Yields:
            True when self sorts after or equal to other, False otherwise.
            INVALID when either operand is not a Str or is a sentinel.

        Example:
            >>> nu.run(nu.Str("apple") >= nu.Str("apple"))[0]
            True
        """
        from nu.core import Ge

        from .bool_ import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: StrArg) -> Bool:
        """Self less than or equal to other, lexicographically.

        Args:
            other: the string to compare against.

        Yields:
            True when self sorts before or equal to other, False otherwise.
            INVALID when either operand is not a Str or is a sentinel.

        Example:
            >>> nu.run(nu.Str("apple") <= nu.Str("banana"))[0]
            True
        """
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: StrArg) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the string to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the strings compare equal, False otherwise. INVALID
            when either operand is not a Str or is a sentinel.

        Example:
            >>> nu.run(nu.Str("hi") == nu.Str("hi"))[0]
            True
        """
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: StrArg) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the string to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the strings differ, False otherwise. INVALID when
            either operand is not a Str or is a sentinel.

        Example:
            >>> nu.run(nu.Str("hi") != nu.Str("bye"))[0]
            True
        """
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))

    def is_(self, other: StrArg) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For scalar comparison
              use `==` instead.
            - Python interns short/literal strings, so distinct Str
              literals with equal text can still test identical.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.Str("abc").is_("abc"))[0]
            True
        """
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: StrArg) -> Bool:
        """Logical AND of self and other.

        Args:
            other: the value to AND with self. Coerced to Bool by
                truthiness (the empty string is False, everything else is
                True).

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.

        Yields:
            True when both operands are truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Str("hi").and_(nu.Str("")))[0]
            False
        """
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: StrArg) -> Bool:
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
            >>> nu.run(nu.Str("").or_(nu.Str("hi")))[0]
            True
        """
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT of self.

        Notes:
            - The empty string yields True, every other string yields
              False.

        Yields:
            True when self is the empty string, False otherwise. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.Str("").not_())[0]
            True
        """
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Cast self to Bool.

        Notes:
            - The empty string becomes False, every other string becomes
              True, matching Python's truthiness rule.

        Yields:
            True when self is non-empty, False when self is empty. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.Str("hi").bool_())[0]
            True
        """
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # CASE TRANSFORMATION
    # =========================================================================

    def upper(self) -> Str:
        """Self converted to uppercase.

        Yields:
            The uppercased string. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("Hello World").upper())[0]
            'HELLO WORLD'
        """
        from .str_interactions import Upper

        return Str(Upper(self))

    def lower(self) -> Str:
        """Self converted to lowercase.

        Yields:
            The lowercased string. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("Hello World").lower())[0]
            'hello world'
        """
        from .str_interactions import Lower

        return Str(Lower(self))

    def title(self) -> Str:
        """Self converted to title case.

        Yields:
            The titlecased string. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("hello world").title())[0]
            'Hello World'
        """
        from .str_interactions import Title

        return Str(Title(self))

    def capitalize(self) -> Str:
        """Self with only the first character capitalized.

        Notes:
            - Every character after the first is lowercased, matching
              Python's `str.capitalize`.

        Yields:
            The capitalized string. INVALID when self is a sentinel or not
            a Str.

        Example:
            >>> nu.run(nu.Str("hello world").capitalize())[0]
            'Hello world'
        """
        from .str_interactions import Capitalize

        return Str(Capitalize(self))

    def swapcase(self) -> Str:
        """Self with uppercase and lowercase characters swapped.

        Yields:
            The case-swapped string. INVALID when self is a sentinel or not
            a Str.

        Example:
            >>> nu.run(nu.Str("Hello World").swapcase())[0]
            'hELLO wORLD'
        """
        from .str_interactions import SwapCase

        return Str(SwapCase(self))

    def casefold(self) -> Str:
        """Self folded for aggressive, caseless matching.

        Notes:
            - Stronger than `lower`: handles cases `lower` misses, like the
              German `ß` folding to `ss`.

        Yields:
            The casefolded string. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("Straße").casefold())[0]
            'strasse'
        """
        from .str_interactions import Casefold

        return Str(Casefold(self))

    # =========================================================================
    # STRIPPING
    # =========================================================================

    def strip(self, chars: StrArg | None = None) -> Str:
        """Self with leading and trailing characters removed.

        Args:
            chars: the set of characters to strip, each considered
                independently. When omitted, strips whitespace.

        Yields:
            The stripped string. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("  hi  ").strip())[0]
            'hi'

            >>> nu.run(nu.Str("xxhixx").strip("x"))[0]
            'hi'
        """
        from .str_interactions import Strip

        return Str(Strip(self, chars))

    def lstrip(self, chars: StrArg | None = None) -> Str:
        """Self with leading characters removed.

        Args:
            chars: the set of characters to strip, each considered
                independently. When omitted, strips whitespace.

        Yields:
            The left-stripped string. INVALID when self is a sentinel or
            not a Str.

        Example:
            >>> nu.run(nu.Str("  hi  ").lstrip())[0]
            'hi  '
        """
        from .str_interactions import LStrip

        return Str(LStrip(self, chars))

    def rstrip(self, chars: StrArg | None = None) -> Str:
        """Self with trailing characters removed.

        Args:
            chars: the set of characters to strip, each considered
                independently. When omitted, strips whitespace.

        Yields:
            The right-stripped string. INVALID when self is a sentinel or
            not a Str.

        Example:
            >>> nu.run(nu.Str("  hi  ").rstrip())[0]
            '  hi'
        """
        from .str_interactions import RStrip

        return Str(RStrip(self, chars))

    # =========================================================================
    # SPLITTING
    # =========================================================================

    def split(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> List:
        """Self split into a list on sep, from the left.

        Args:
            sep: the separator to split on. When omitted, splits on runs of
                whitespace and drops empty strings from the result.
            maxsplit: the maximum number of splits. `-1` means unlimited.

        Yields:
            The list of pieces. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("a,b,c").split(","))[0]
            ['a', 'b', 'c']

            >>> nu.run(nu.Str("a,b,c").split(",", 1))[0]
            ['a', 'b,c']
        """
        from ..collections.list_ import List
        from .str_interactions import Split

        return List(Split(self, sep, maxsplit))

    def rsplit(self, sep: StrArg | None = None, maxsplit: IntArg = -1) -> List:
        """Self split into a list on sep, from the right.

        Args:
            sep: the separator to split on. When omitted, splits on runs of
                whitespace and drops empty strings from the result.
            maxsplit: the maximum number of splits. `-1` means unlimited.

        Notes:
            - Only differs from `split` when `maxsplit` is bounded: the
              splits are taken starting from the right end of the string.

        Yields:
            The list of pieces. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("a,b,c").rsplit(",", 1))[0]
            ['a,b', 'c']
        """
        from ..collections.list_ import List
        from .str_interactions import RSplit

        return List(RSplit(self, sep, maxsplit))

    def splitlines(self, keepends: BoolArg = False) -> List:
        r"""Self split into a list at line boundaries.

        Args:
            keepends: when True, keeps the line-ending characters at the
                end of each piece instead of dropping them.

        Yields:
            The list of lines. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("a\nb\nc").splitlines())[0]
            ['a', 'b', 'c']
        """
        from ..collections.list_ import List
        from .str_interactions import SplitLines

        return List(SplitLines(self, keepends))

    def partition(self, sep: StrArg) -> Tuple:
        """Self split around the first occurrence of sep into a 3-tuple.

        Args:
            sep: the separator to split on.

        Notes:
            - The 3-tuple is always `(before, sep, after)`. When sep is not
              found, that's `(self, "", "")`.

        Yields:
            The 3-tuple of pieces. INVALID when self is a sentinel, not a
            Str, or sep is empty.

        Example:
            >>> nu.run(nu.Str("a,b,c").partition(","))[0]
            ('a', ',', 'b,c')
        """
        from ..collections.tuple_ import Tuple
        from .str_interactions import Partition

        return Tuple(Partition(self, sep))

    def rpartition(self, sep: StrArg) -> Tuple:
        """Self split around the last occurrence of sep into a 3-tuple.

        Args:
            sep: the separator to split on.

        Notes:
            - The 3-tuple is always `(before, sep, after)`. When sep is not
              found, that's `("", "", self)`.

        Yields:
            The 3-tuple of pieces. INVALID when self is a sentinel, not a
            Str, or sep is empty.

        Example:
            >>> nu.run(nu.Str("a,b,c").rpartition(","))[0]
            ('a,b', ',', 'c')
        """
        from ..collections.tuple_ import Tuple
        from .str_interactions import RPartition

        return Tuple(RPartition(self, sep))

    # =========================================================================
    # SEARCHING
    # =========================================================================

    def find(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Lowest index in self where sub is found, searching from the left.

        Args:
            sub: the substring to search for.
            start: the index to start searching from.
            end: the index to stop searching at. Searches to the end of
                the string when omitted.

        Yields:
            The lowest matching index, or `-1` when sub is not found.
            INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("hello world").find("o"))[0]
            4

            >>> nu.run(nu.Str("hello world").find("z"))[0]
            -1
        """
        from .int_ import Int
        from .str_interactions import Find

        return Int(Find(self, sub, start, end))

    def rfind(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Highest index in self where sub is found, searching from the right.

        Args:
            sub: the substring to search for.
            start: the index to start searching from.
            end: the index to stop searching at. Searches to the end of
                the string when omitted.

        Yields:
            The highest matching index, or `-1` when sub is not found.
            INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("hello world").rfind("o"))[0]
            7
        """
        from .int_ import Int
        from .str_interactions import RFind

        return Int(RFind(self, sub, start, end))

    def index(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Lowest index in self where sub is found, searching from the left.

        Args:
            sub: the substring to search for.
            start: the index to start searching from.
            end: the index to stop searching at. Searches to the end of
                the string when omitted.

        Notes:
            - Unlike Python's `str.index`, a missing sub does not raise: it
              yields INVALID instead. Use `find` if `-1` on a miss is the
              behaviour you want.

        Yields:
            The lowest matching index. INVALID when self is a sentinel, not
            a Str, or sub is not found.

        Example:
            >>> nu.run(nu.Str("hello world").index("o"))[0]
            4
        """
        from .int_ import Int
        from .str_interactions import Index

        return Int(Index(self, sub, start, end))

    def rindex(self, sub: StrArg, start: IntArg = 0, end: IntArg | None = None) -> Int:
        """Highest index in self where sub is found, searching from the right.

        Args:
            sub: the substring to search for.
            start: the index to start searching from.
            end: the index to stop searching at. Searches to the end of
                the string when omitted.

        Notes:
            - Unlike Python's `str.rindex`, a missing sub does not raise:
              it yields INVALID instead. Use `rfind` if `-1` on a miss is
              the behaviour you want.

        Yields:
            The highest matching index. INVALID when self is a sentinel,
            not a Str, or sub is not found.

        Example:
            >>> nu.run(nu.Str("hello world").rindex("o"))[0]
            7
        """
        from .int_ import Int
        from .str_interactions import RIndex

        return Int(RIndex(self, sub, start, end))

    def count_substring(self, sub: StrArg) -> Int:
        """Count of non-overlapping occurrences of sub in self.

        Args:
            sub: the substring to count.

        Yields:
            The occurrence count. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("banana").count_substring("an"))[0]
            2
        """
        from .int_ import Int
        from .str_interactions import CountSubstring

        return Int(CountSubstring(self, sub))

    # =========================================================================
    # TESTING
    # =========================================================================

    def startswith(self, prefix: StrArg) -> Bool:
        """Whether self starts with prefix.

        Args:
            prefix: the string to test for at the start of self.

        Yields:
            True when self starts with prefix, False otherwise. INVALID
            when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("hello").startswith("he"))[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import StartsWith

        return Bool(StartsWith(self, prefix))

    def endswith(self, suffix: StrArg) -> Bool:
        """Whether self ends with suffix.

        Args:
            suffix: the string to test for at the end of self.

        Yields:
            True when self ends with suffix, False otherwise. INVALID when
            self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("hello").endswith("lo"))[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import EndsWith

        return Bool(EndsWith(self, suffix))

    def isdigit(self) -> Bool:
        """Whether every character in self is a digit.

        Yields:
            True when self is non-empty and every character is a digit,
            False otherwise. INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("123").isdigit())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsDigit

        return Bool(IsDigit(self))

    def isalpha(self) -> Bool:
        """Whether every character in self is alphabetic.

        Yields:
            True when self is non-empty and every character is alphabetic,
            False otherwise. INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("abc").isalpha())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsAlpha

        return Bool(IsAlpha(self))

    def isalnum(self) -> Bool:
        """Whether every character in self is alphanumeric.

        Yields:
            True when self is non-empty and every character is alphanumeric,
            False otherwise. INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("abc123").isalnum())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsAlnum

        return Bool(IsAlnum(self))

    def isspace(self) -> Bool:
        """Whether every character in self is whitespace.

        Yields:
            True when self is non-empty and every character is whitespace,
            False otherwise. INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("   ").isspace())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsSpace

        return Bool(IsSpace(self))

    def isnumeric(self) -> Bool:
        """Whether every character in self is numeric.

        Notes:
            - Broader than `isdigit`: also true for characters like
              fractions and Unicode numerals that `isdigit` rejects.

        Yields:
            True when self is non-empty and every character is numeric,
            False otherwise. INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("123").isnumeric())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsNumeric

        return Bool(IsNumeric(self))

    def isdecimal(self) -> Bool:
        """Whether every character in self is a decimal character.

        Notes:
            - Narrower than `isnumeric`: only characters that can form
              base-10 numbers qualify.

        Yields:
            True when self is non-empty and every character is decimal,
            False otherwise. INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("123").isdecimal())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsDecimal

        return Bool(IsDecimal(self))

    def isidentifier(self) -> Bool:
        """Whether self is a valid Python identifier.

        Yields:
            True when self would be a legal Python identifier, False
            otherwise. INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("my_var").isidentifier())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsIdentifier

        return Bool(IsIdentifier(self))

    def isprintable(self) -> Bool:
        """Whether every character in self is printable.

        Notes:
            - The empty string is printable; it's the presence of
              non-printable characters (like control characters) that
              makes this False.

        Yields:
            True when every character is printable, False otherwise.
            INVALID when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("abc").isprintable())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsPrintable

        return Bool(IsPrintable(self))

    def istitle(self) -> Bool:
        """Whether self is titlecased.

        Yields:
            True when self is non-empty and titlecased (each word starts
            uppercase, the rest lowercase), False otherwise. INVALID when
            self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("Hello World").istitle())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsTitle

        return Bool(IsTitle(self))

    def isupper(self) -> Bool:
        """Whether every cased character in self is uppercase.

        Yields:
            True when self has at least one cased character and all of
            them are uppercase, False otherwise. INVALID when self is a
            sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("ABC").isupper())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsUpper

        return Bool(IsUpper(self))

    def islower(self) -> Bool:
        """Whether every cased character in self is lowercase.

        Yields:
            True when self has at least one cased character and all of
            them are lowercase, False otherwise. INVALID when self is a
            sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("abc").islower())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsLower

        return Bool(IsLower(self))

    def isascii(self) -> Bool:
        """Whether every character in self is ASCII.

        Notes:
            - Unlike the other `is*` checks, the empty string yields True
              here rather than False.

        Yields:
            True when every character is ASCII, False otherwise. INVALID
            when self is a sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("").isascii())[0]
            True
        """
        from .bool_ import Bool
        from .str_interactions import IsAscii

        return Bool(IsAscii(self))

    # =========================================================================
    # PADDING
    # =========================================================================

    def center(self, width: IntArg, fillchar: StrArg = " ") -> Str:
        """Self centered in a field of the given width.

        Args:
            width: the total width of the result. Self is returned
                unchanged when it's already at least this wide.
            fillchar: the padding character.

        Notes:
            - fillchar must be exactly one character; anything else yields
              INVALID rather than raising.

        Yields:
            The centered string. INVALID when self is a sentinel, not a
            Str, or fillchar is not a single character.

        Example:
            >>> nu.run(nu.Str("hi").center(6, "*"))[0]
            '**hi**'
        """
        from .str_interactions import Center

        return Str(Center(self, width, fillchar))

    def ljust(self, width: IntArg, fillchar: StrArg = " ") -> Str:
        """Self left-justified in a field of the given width.

        Args:
            width: the total width of the result. Self is returned
                unchanged when it's already at least this wide.
            fillchar: the padding character.

        Notes:
            - fillchar must be exactly one character; anything else yields
              INVALID rather than raising.

        Yields:
            The left-justified string. INVALID when self is a sentinel, not
            a Str, or fillchar is not a single character.

        Example:
            >>> nu.run(nu.Str("hi").ljust(6, "*"))[0]
            'hi****'
        """
        from .str_interactions import LJust

        return Str(LJust(self, width, fillchar))

    def rjust(self, width: IntArg, fillchar: StrArg = " ") -> Str:
        """Self right-justified in a field of the given width.

        Args:
            width: the total width of the result. Self is returned
                unchanged when it's already at least this wide.
            fillchar: the padding character.

        Notes:
            - fillchar must be exactly one character; anything else yields
              INVALID rather than raising.

        Yields:
            The right-justified string. INVALID when self is a sentinel,
            not a Str, or fillchar is not a single character.

        Example:
            >>> nu.run(nu.Str("hi").rjust(6, "*"))[0]
            '****hi'
        """
        from .str_interactions import RJust

        return Str(RJust(self, width, fillchar))

    def zfill(self, width: IntArg) -> Str:
        """Self padded with leading zeros to the given width.

        Args:
            width: the total width of the result. Self is returned
                unchanged when it's already at least this wide.

        Notes:
            - A leading sign (`+` or `-`) stays in front of the zeros
              rather than being padded over, matching Python's
              `str.zfill`.

        Yields:
            The zero-filled string. INVALID when self is a sentinel or not
            a Str.

        Example:
            >>> nu.run(nu.Str("-42").zfill(5))[0]
            '-0042'
        """
        from .str_interactions import ZFill

        return Str(ZFill(self, width))

    def expandtabs(self, tabsize: IntArg = 8) -> Str:
        r"""Self with tab characters expanded to spaces.

        Args:
            tabsize: the number of columns between tab stops.

        Yields:
            The expanded string. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("a\tb").expandtabs(4))[0]
            'a   b'
        """
        from .str_interactions import ExpandTabs

        return Str(ExpandTabs(self, tabsize))

    # =========================================================================
    # REPLACING
    # =========================================================================

    def replace(self, old: StrArg, new: StrArg, count: IntArg = -1) -> Str:
        """Self with occurrences of old replaced by new.

        Args:
            old: the substring to replace.
            new: the replacement substring.
            count: the maximum number of occurrences to replace. `-1`
                means replace all of them.

        Yields:
            The replaced string. INVALID when self is a sentinel or not a
            Str.

        Example:
            >>> nu.run(nu.Str("hello world").replace("o", "0"))[0]
            'hell0 w0rld'

            >>> nu.run(nu.Str("hello world").replace("o", "0", 1))[0]
            'hell0 world'
        """
        from .str_interactions import Replace

        return Str(Replace(self, old, new, count))

    def removeprefix(self, prefix: StrArg) -> Str:
        """Self with the given prefix removed if present.

        Args:
            prefix: the prefix to strip. Self is returned unchanged when it
                doesn't start with prefix.

        Yields:
            The string with prefix removed. INVALID when self is a
            sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("hello.txt").removeprefix("hello"))[0]
            '.txt'
        """
        from .str_interactions import RemovePrefix

        return Str(RemovePrefix(self, prefix))

    def removesuffix(self, suffix: StrArg) -> Str:
        """Self with the given suffix removed if present.

        Args:
            suffix: the suffix to strip. Self is returned unchanged when it
                doesn't end with suffix.

        Yields:
            The string with suffix removed. INVALID when self is a
            sentinel or not a Str.

        Example:
            >>> nu.run(nu.Str("hello.txt").removesuffix(".txt"))[0]
            'hello'
        """
        from .str_interactions import RemoveSuffix

        return Str(RemoveSuffix(self, suffix))

    def translate(self, table: DictArg) -> Str:
        """Self with characters mapped through a translation table.

        Args:
            table: a mapping from Unicode ordinal to replacement ordinal,
                string, or None to delete the character.

        Notes:
            - A malformed table (bad ordinal, bad replacement type) yields
              INVALID rather than raising.

        Yields:
            The translated string. INVALID when self is a sentinel, not a
            Str, or table is malformed.

        Example:
            >>> nu.run(nu.Str("hello").translate({104: 72}))[0]
            'Hello'
        """
        from .str_interactions import Translate

        return Str(Translate(self, table))

    # =========================================================================
    # FORMATTING
    # =========================================================================

    def format_map(self, mapping: DictArg) -> Str:
        """Self formatted with `{field}` placeholders filled from mapping.

        Args:
            mapping: the field-name to value mapping, used as `str.format`
                would use `**kwargs`.

        Notes:
            - A missing field, or any other formatting error, yields
              INVALID rather than raising.

        Yields:
            The formatted string. INVALID when self is a sentinel, not a
            Str, or formatting fails.

        Example:
            >>> nu.run(nu.Str("{name} is {age}").format_map({"name": "Nu", "age": 1}))[0]
            'Nu is 1'
        """
        from .str_interactions import FormatMap

        return Str(FormatMap(self, mapping))

    # =========================================================================
    # ENCODING
    # =========================================================================

    def encode(self, encoding: StrArg = "utf-8") -> Bytes:
        """Self encoded to Bytes.

        Args:
            encoding: the codec to encode with, by name.

        Notes:
            - A character that can't be represented in the given encoding,
              or an unknown encoding name, yields INVALID rather than
              raising.

        Yields:
            The encoded bytes. INVALID when self is a sentinel, not a Str,
            or encoding fails.

        Example:
            >>> nu.run(nu.Str("hello").encode())[0]
            b'hello'
        """
        from .bytes_ import Bytes
        from .str_interactions import Encode

        return Bytes(Encode(self, encoding))

    # =========================================================================
    # JOINING
    # =========================================================================

    def join(self, iterable: object) -> Str:
        """Elements of iterable joined together with self as separator.

        Args:
            iterable: the strings to join. Every element must be a string.

        Notes:
            - A non-string element yields INVALID rather than raising.

        Yields:
            The joined string. INVALID when self is a sentinel, not a Str,
            or iterable contains a non-string element.

        Example:
            >>> nu.run(nu.Str(", ").join(["a", "b", "c"]))[0]
            'a, b, c'
        """
        from .str_interactions import Join

        return Str(Join(self, iterable))
