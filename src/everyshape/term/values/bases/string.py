"""String base classes for RValue types.

This module provides string operation mixins including:
- ConcatenableBase - __add__ for strings
- StringMethodsBase - String-specific methods
- StringBase - Combined base for string-like values
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..conversion import literal
from .arithmetic import AddableBase
from .collection import ContainableBase, LengthableBase, SliceableBase


if TYPE_CHECKING:
    from ...term import RValue
    from ..values import BoolValue, BytesValue, IntValue, ListValue


__all__ = [
    "ConcatenableBase",
    "StringBase",
    "StringMethodsBase",
]


class ConcatenableBase[OperandT, ResultT](AddableBase[OperandT, ResultT]):
    """Base for values that support concatenation via +.

    Same as AddableBase but semantically for string-like concatenation.
    """

    pass


class StringMethodsBase[ResultT]:
    """Base providing string-specific methods.

    Methods that return strings use _wrap_string_result() for subclass customization.
    Methods that return bool/int use specific types.
    """

    def _wrap_string_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    # Case transformation
    def upper(self) -> ResultT:
        """Convert to uppercase.

        Returns:
            Uppercase string
        """
        from ...comps.types.string import UpperOp

        return cast("ResultT", self._wrap_string_result(UpperOp(self)))

    def lower(self) -> ResultT:
        """Convert to lowercase.

        Returns:
            Lowercase string
        """
        from ...comps.types.string import LowerOp

        return cast("ResultT", self._wrap_string_result(LowerOp(self)))

    def title(self) -> ResultT:
        """Convert to title case.

        Returns:
            Title-cased string
        """
        from ...comps.types.string import TitleOp

        return cast("ResultT", self._wrap_string_result(TitleOp(self)))

    def capitalize(self) -> ResultT:
        """Capitalize first character.

        Returns:
            Capitalized string
        """
        from ...comps.types.string import CapitalizeOp

        return cast("ResultT", self._wrap_string_result(CapitalizeOp(self)))

    def swapcase(self) -> ResultT:
        """Swap case.

        Returns:
            Case-swapped string
        """
        from ...comps.types.string import SwapCaseOp

        return cast("ResultT", self._wrap_string_result(SwapCaseOp(self)))

    # Stripping
    def strip(self, chars: str | RValue | None = None) -> ResultT:
        """Strip whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped string
        """
        from ...comps.types.string import StripOp

        if chars is not None:
            return cast("ResultT", self._wrap_string_result(StripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_string_result(StripOp(self)))

    def lstrip(self, chars: str | RValue | None = None) -> ResultT:
        """Strip leading whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped string
        """
        from ...comps.types.string import LStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_string_result(LStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_string_result(LStripOp(self)))

    def rstrip(self, chars: str | RValue | None = None) -> ResultT:
        """Strip trailing whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped string
        """
        from ...comps.types.string import RStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_string_result(RStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_string_result(RStripOp(self)))

    # Splitting
    def split(self, sep: str | RValue | None = None, maxsplit: int = -1) -> ListValue[str]:
        """Split string.

        Args:
            sep: Separator (None for whitespace)
            maxsplit: Maximum splits (-1 for unlimited)

        Returns:
            List of substrings
        """
        from ...comps.types.string import SplitOp
        from ..values import ListValue

        if sep is not None:
            return ListValue(SplitOp(self, literal(sep), maxsplit))
        return ListValue(SplitOp(self, None, maxsplit))

    def rsplit(self, sep: str | RValue | None = None, maxsplit: int = -1) -> ListValue[str]:
        """Right split string.

        Args:
            sep: Separator (None for whitespace)
            maxsplit: Maximum splits (-1 for unlimited)

        Returns:
            List of substrings
        """
        from ...comps.types.string import RSplitOp
        from ..values import ListValue

        if sep is not None:
            return ListValue(RSplitOp(self, literal(sep), maxsplit))
        return ListValue(RSplitOp(self, None, maxsplit))

    # Searching
    def find(self, sub: str | RValue, start: int = 0, end: int | None = None) -> IntValue:
        """Find substring.

        Args:
            sub: Substring to find
            start: Start index
            end: End index

        Returns:
            Index or -1 if not found
        """
        from ...comps.types.string import FindOp
        from ..values import IntValue

        return IntValue(FindOp(self, literal(sub), start, end))

    def rfind(self, sub: str | RValue, start: int = 0, end: int | None = None) -> IntValue:
        """Find substring from right.

        Args:
            sub: Substring to find
            start: Start index
            end: End index

        Returns:
            Index or -1 if not found
        """
        from ...comps.types.string import RFindOp
        from ..values import IntValue

        return IntValue(RFindOp(self, literal(sub), start, end))

    def count_substring(self, sub: str | RValue) -> IntValue:
        """Count substring occurrences.

        Args:
            sub: Substring to count

        Returns:
            Count
        """
        from ...comps.types.string import CountSubstringOp
        from ..values import IntValue

        return IntValue(CountSubstringOp(self, literal(sub)))

    # Testing
    def startswith(self, prefix: str | RValue) -> BoolValue:
        """Check if starts with prefix.

        Args:
            prefix: Prefix to check

        Returns:
            Boolean result
        """
        from ...comps.types.string import StartsWithOp
        from ..values import BoolValue

        return BoolValue(StartsWithOp(self, literal(prefix)))

    def endswith(self, suffix: str | RValue) -> BoolValue:
        """Check if ends with suffix.

        Args:
            suffix: Suffix to check

        Returns:
            Boolean result
        """
        from ...comps.types.string import EndsWithOp
        from ..values import BoolValue

        return BoolValue(EndsWithOp(self, literal(suffix)))

    def isdigit(self) -> BoolValue:
        """Check if all digits.

        Returns:
            Boolean result
        """
        from ...comps.types.string import IsDigitOp
        from ..values import BoolValue

        return BoolValue(IsDigitOp(self))

    def isalpha(self) -> BoolValue:
        """Check if all alphabetic.

        Returns:
            Boolean result
        """
        from ...comps.types.string import IsAlphaOp
        from ..values import BoolValue

        return BoolValue(IsAlphaOp(self))

    def isalnum(self) -> BoolValue:
        """Check if alphanumeric.

        Returns:
            Boolean result
        """
        from ...comps.types.string import IsAlnumOp
        from ..values import BoolValue

        return BoolValue(IsAlnumOp(self))

    def isspace(self) -> BoolValue:
        """Check if all whitespace.

        Returns:
            Boolean result
        """
        from ...comps.types.string import IsSpaceOp
        from ..values import BoolValue

        return BoolValue(IsSpaceOp(self))

    # Padding
    def center(self, width: int | RValue, fillchar: str = " ") -> ResultT:
        """Center in width.

        Args:
            width: Target width
            fillchar: Fill character

        Returns:
            Centered string
        """
        from ...comps.types.string import CenterOp

        return cast("ResultT", self._wrap_string_result(CenterOp(self, literal(width), fillchar)))

    def ljust(self, width: int | RValue, fillchar: str = " ") -> ResultT:
        """Left justify.

        Args:
            width: Target width
            fillchar: Fill character

        Returns:
            Left-justified string
        """
        from ...comps.types.string import LJustOp

        return cast("ResultT", self._wrap_string_result(LJustOp(self, literal(width), fillchar)))

    def rjust(self, width: int | RValue, fillchar: str = " ") -> ResultT:
        """Right justify.

        Args:
            width: Target width
            fillchar: Fill character

        Returns:
            Right-justified string
        """
        from ...comps.types.string import RJustOp

        return cast("ResultT", self._wrap_string_result(RJustOp(self, literal(width), fillchar)))

    def zfill(self, width: int | RValue) -> ResultT:
        """Zero-fill.

        Args:
            width: Target width

        Returns:
            Zero-filled string
        """
        from ...comps.types.string import ZFillOp

        return cast("ResultT", self._wrap_string_result(ZFillOp(self, literal(width))))

    # Replacing
    def replace(self, old: str | RValue, new: str | RValue, count: int = -1) -> ResultT:
        """Replace substring.

        Args:
            old: String to replace
            new: Replacement string
            count: Maximum replacements (-1 for all)

        Returns:
            Modified string
        """
        from ...comps.types.string import ReplaceOp

        return cast(
            "ResultT",
            self._wrap_string_result(ReplaceOp(self, literal(old), literal(new), count)),
        )

    # Encoding
    def encode(self, encoding: str = "utf-8") -> BytesValue:
        """Encode string to bytes.

        Args:
            encoding: Character encoding

        Returns:
            Encoded bytes
        """
        from ...comps.types.string import EncodeOp
        from ..values import BytesValue

        return BytesValue(EncodeOp(self, encoding))


class StringBase[ResultT](
    ConcatenableBase[str, ResultT],
    LengthableBase,
    SliceableBase[ResultT],
    ContainableBase[str],
    StringMethodsBase[ResultT],
):
    """Combined base for string-like values.

    Provides: + (concatenation), len_(), slice_(), contains(),
    plus all string-specific operations from StringMethodsBase.

    Subclasses typically also implement __getitem__ for indexing.
    """

    pass
