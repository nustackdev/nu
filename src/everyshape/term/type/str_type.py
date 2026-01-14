"""String types for Term expressions.

This module provides string operation mixins and StrType including:
- ConcatenableBase - __add__ for strings
- StringMethodsBase - String-specific methods
- StringBase - Combined base for string-like values
- StrType - String type for Term expressions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..conversion import literal
from .base_arithmetic import AddableBase
from .base_collections import ContainableBase, LengthableBase, SliceableBase
from .base_comparison import ComparisonBase
from .base_logical import LogicalBase
from .type import Type


if TYPE_CHECKING:
    from ..term import Term
    from .bool_type import BoolType
    from .bytes_type import BytesType
    from .int_type import IntType
    from .list_type import ListType


__all__ = [
    "ConcatenableBase",
    "StrType",
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

    def _wrap_string_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    # Case transformation
    def upper(self) -> ResultT:
        """Convert to uppercase.

        Returns:
            Uppercase string
        """
        from ..comps.typed.string import UpperOp

        return cast("ResultT", self._wrap_string_result(UpperOp(self)))

    def lower(self) -> ResultT:
        """Convert to lowercase.

        Returns:
            Lowercase string
        """
        from ..comps.typed.string import LowerOp

        return cast("ResultT", self._wrap_string_result(LowerOp(self)))

    def title(self) -> ResultT:
        """Convert to title case.

        Returns:
            Title-cased string
        """
        from ..comps.typed.string import TitleOp

        return cast("ResultT", self._wrap_string_result(TitleOp(self)))

    def capitalize(self) -> ResultT:
        """Capitalize first character.

        Returns:
            Capitalized string
        """
        from ..comps.typed.string import CapitalizeOp

        return cast("ResultT", self._wrap_string_result(CapitalizeOp(self)))

    def swapcase(self) -> ResultT:
        """Swap case.

        Returns:
            Case-swapped string
        """
        from ..comps.typed.string import SwapCaseOp

        return cast("ResultT", self._wrap_string_result(SwapCaseOp(self)))

    # Stripping
    def strip(self, chars: str | Term | None = None) -> ResultT:
        """Strip whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped string
        """
        from ..comps.typed.string import StripOp

        if chars is not None:
            return cast("ResultT", self._wrap_string_result(StripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_string_result(StripOp(self)))

    def lstrip(self, chars: str | Term | None = None) -> ResultT:
        """Strip leading whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped string
        """
        from ..comps.typed.string import LStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_string_result(LStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_string_result(LStripOp(self)))

    def rstrip(self, chars: str | Term | None = None) -> ResultT:
        """Strip trailing whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped string
        """
        from ..comps.typed.string import RStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_string_result(RStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_string_result(RStripOp(self)))

    # Splitting
    def split(self, sep: str | Term | None = None, maxsplit: int = -1) -> ListType[str]:
        """Split string.

        Args:
            sep: Separator (None for whitespace)
            maxsplit: Maximum splits (-1 for unlimited)

        Returns:
            List of substrings
        """
        from ..comps.typed.string import SplitOp
        from .list_type import ListType

        if sep is not None:
            return ListType(SplitOp(self, literal(sep), maxsplit))
        return ListType(SplitOp(self, None, maxsplit))

    def rsplit(self, sep: str | Term | None = None, maxsplit: int = -1) -> ListType[str]:
        """Right split string.

        Args:
            sep: Separator (None for whitespace)
            maxsplit: Maximum splits (-1 for unlimited)

        Returns:
            List of substrings
        """
        from ..comps.typed.string import RSplitOp
        from .list_type import ListType

        if sep is not None:
            return ListType(RSplitOp(self, literal(sep), maxsplit))
        return ListType(RSplitOp(self, None, maxsplit))

    # Searching
    def find(self, sub: str | Term, start: int = 0, end: int | None = None) -> IntType:
        """Find substring.

        Args:
            sub: Substring to find
            start: Start index
            end: End index

        Returns:
            Index or -1 if not found
        """
        from ..comps.typed.string import FindOp
        from .int_type import IntType

        return IntType(FindOp(self, literal(sub), start, end))

    def rfind(self, sub: str | Term, start: int = 0, end: int | None = None) -> IntType:
        """Find substring from right.

        Args:
            sub: Substring to find
            start: Start index
            end: End index

        Returns:
            Index or -1 if not found
        """
        from ..comps.typed.string import RFindOp
        from .int_type import IntType

        return IntType(RFindOp(self, literal(sub), start, end))

    def count_substring(self, sub: str | Term) -> IntType:
        """Count substring occurrences.

        Args:
            sub: Substring to count

        Returns:
            Count
        """
        from ..comps.typed.string import CountSubstringOp
        from .int_type import IntType

        return IntType(CountSubstringOp(self, literal(sub)))

    # Testing
    def startswith(self, prefix: str | Term) -> BoolType:
        """Check if starts with prefix.

        Args:
            prefix: Prefix to check

        Returns:
            Boolean result
        """
        from ..comps.typed.string import StartsWithOp
        from .bool_type import BoolType

        return BoolType(StartsWithOp(self, literal(prefix)))

    def endswith(self, suffix: str | Term) -> BoolType:
        """Check if ends with suffix.

        Args:
            suffix: Suffix to check

        Returns:
            Boolean result
        """
        from ..comps.typed.string import EndsWithOp
        from .bool_type import BoolType

        return BoolType(EndsWithOp(self, literal(suffix)))

    def isdigit(self) -> BoolType:
        """Check if all digits.

        Returns:
            Boolean result
        """
        from ..comps.typed.string import IsDigitOp
        from .bool_type import BoolType

        return BoolType(IsDigitOp(self))

    def isalpha(self) -> BoolType:
        """Check if all alphabetic.

        Returns:
            Boolean result
        """
        from ..comps.typed.string import IsAlphaOp
        from .bool_type import BoolType

        return BoolType(IsAlphaOp(self))

    def isalnum(self) -> BoolType:
        """Check if alphanumeric.

        Returns:
            Boolean result
        """
        from ..comps.typed.string import IsAlnumOp
        from .bool_type import BoolType

        return BoolType(IsAlnumOp(self))

    def isspace(self) -> BoolType:
        """Check if all whitespace.

        Returns:
            Boolean result
        """
        from ..comps.typed.string import IsSpaceOp
        from .bool_type import BoolType

        return BoolType(IsSpaceOp(self))

    # Padding
    def center(self, width: int | Term, fillchar: str = " ") -> ResultT:
        """Center in width.

        Args:
            width: Target width
            fillchar: Fill character

        Returns:
            Centered string
        """
        from ..comps.typed.string import CenterOp

        return cast("ResultT", self._wrap_string_result(CenterOp(self, literal(width), fillchar)))

    def ljust(self, width: int | Term, fillchar: str = " ") -> ResultT:
        """Left justify.

        Args:
            width: Target width
            fillchar: Fill character

        Returns:
            Left-justified string
        """
        from ..comps.typed.string import LJustOp

        return cast("ResultT", self._wrap_string_result(LJustOp(self, literal(width), fillchar)))

    def rjust(self, width: int | Term, fillchar: str = " ") -> ResultT:
        """Right justify.

        Args:
            width: Target width
            fillchar: Fill character

        Returns:
            Right-justified string
        """
        from ..comps.typed.string import RJustOp

        return cast("ResultT", self._wrap_string_result(RJustOp(self, literal(width), fillchar)))

    def zfill(self, width: int | Term) -> ResultT:
        """Zero-fill.

        Args:
            width: Target width

        Returns:
            Zero-filled string
        """
        from ..comps.typed.string import ZFillOp

        return cast("ResultT", self._wrap_string_result(ZFillOp(self, literal(width))))

    # Replacing
    def replace(self, old: str | Term, new: str | Term, count: int = -1) -> ResultT:
        """Replace substring.

        Args:
            old: String to replace
            new: Replacement string
            count: Maximum replacements (-1 for all)

        Returns:
            Modified string
        """
        from ..comps.typed.string import ReplaceOp

        return cast(
            "ResultT",
            self._wrap_string_result(ReplaceOp(self, literal(old), literal(new), count)),
        )

    # Encoding
    def encode(self, encoding: str = "utf-8") -> BytesType:
        """Encode string to bytes.

        Args:
            encoding: Character encoding

        Returns:
            Encoded bytes
        """
        from ..comps.typed.string import EncodeOp
        from .bytes_type import BytesType

        return BytesType(EncodeOp(self, encoding))


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


class StrType(
    StringBase["StrType"],
    ComparisonBase["str | StrType"],
    LogicalBase["str | StrType", "BoolType"],
    Type[str],
):
    """String type - represents str expressions (literal or computed).

    Supports concatenation, string operations, comparison, and logical operations.

    Example:
        >>> x = StrType("hello")
        >>> y = x + " world"  # Returns StrType
        >>> z = x.upper()  # Returns StrType
    """

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool_type import BoolType

        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from .bool_type import BoolType

        return BoolType(operand)

    def _wrap_string_result(self, operand: Term) -> Term:
        return StrType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        return StrType(operand)

    def __add__(self, other: str | StrType) -> StrType:
        from ..comps.core.binary_ops import AddOp

        return StrType(AddOp(self, literal(other)))

    def __radd__(self, other: str) -> StrType:
        from ..comps.core.binary_ops import AddOp

        return StrType(AddOp(literal(other), self))
