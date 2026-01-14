"""String operations for Term expressions.

This module provides type-safe operations on string Terms:

Case transformation: UpperOp, LowerOp, TitleOp, CapitalizeOp, SwapCaseOp
Stripping: StripOp, LStripOp, RStripOp
Splitting: SplitOp, RSplitOp
Searching: FindOp, RFindOp, CountSubstringOp
Padding: CenterOp, LJustOp, RJustOp, ZFillOp
Testing: StartsWithOp, EndsWithOp, IsDigitOp, IsAlphaOp, IsAlnumOp, IsSpaceOp
Replacing: ReplaceOp
Encoding: EncodeOp

Design principles:
1. Atomic classes: one operation = one class
2. Runtime type checking: validate input is string at execution
3. Special value propagation: Empty/NaN flow through operations
4. Type safety: preserve return types

Usage:
    # Direct instantiation
    UpperOp(name.get())
    SplitOp(text.get(), ",")

    # Via ergonomics mixin
    name.get().upper()
    text.get().split(",")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.typing import NAN, Sentinel

from ...term import Operation


if TYPE_CHECKING:
    from ...context import Context
    from ...term import Term
    from ...types.__init__1 import UnionBaseType


__all__ = [
    "CapitalizeOp",
    "CenterOp",
    "CountSubstringOp",
    "EncodeOp",
    "EndsWithOp",
    "FindOp",
    "IsAlnumOp",
    "IsAlphaOp",
    "IsDigitOp",
    "IsSpaceOp",
    "LJustOp",
    "LStripOp",
    "LowerOp",
    "RFindOp",
    "RJustOp",
    "RSplitOp",
    "RStripOp",
    "ReplaceOp",
    "SplitOp",
    "StartsWithOp",
    "StripOp",
    "SwapCaseOp",
    "TitleOp",
    "UpperOp",
    "ZFillOp",
]


# =============================================================================
# ABSTRACT STRING OPERATION
# =============================================================================


type OpArgument = Term | UnionBaseType


class StringOp[ResultT](Operation[ResultT]):
    """Base class for string operations.

    Defines execution pattern: evaluate operand → validate string →
    apply operation → return result.
    """

    def __init__(self, operand: OpArgument) -> None:
        """Initialize string operation.

        Args:
            operand: Term that should produce a string
        """
        self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> ResultT:
        """Execute string operation.

        Args:
            context: Execution context

        Returns:
            Operation result
        """
        operand_val = self.children[0].execute(context)
        return self._apply_op(operand_val)

    def _apply_op(self, operand: object) -> ResultT:
        """Apply the operation to operand.

        Subclasses override with operation-specific logic.

        Args:
            operand: The evaluated string

        Returns:
            Operation result
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r})"


# =============================================================================
# CASE TRANSFORMATION OPERATIONS
# =============================================================================


class UpperOp(StringOp[str | Sentinel]):
    """Convert to uppercase: str.upper()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.upper()


class LowerOp(StringOp[str | Sentinel]):
    """Convert to lowercase: str.lower()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.lower()


class TitleOp(StringOp[str | Sentinel]):
    """Convert to title case: str.title()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.title()


class CapitalizeOp(StringOp[str | Sentinel]):
    """Capitalize first character: str.capitalize()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.capitalize()


class SwapCaseOp(StringOp[str | Sentinel]):
    """Swap case: str.swapcase()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.swapcase()


# =============================================================================
# STRIPPING OPERATIONS
# =============================================================================


class StripOp(StringOp[str | Sentinel]):
    """Strip whitespace or chars: str.strip(chars)."""

    def __init__(self, operand: OpArgument, chars: OpArgument | None = None) -> None:
        """Initialize strip operation.

        Args:
            operand: String to strip
            chars: Characters to strip (None for whitespace)
        """
        if chars is not None:
            self.children = (cast("Term", operand), cast("Term", chars))
        else:
            self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> str | Sentinel:
        """Execute strip operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, str):
            return NAN

        if len(self.children) > 1:
            chars_val = self.children[1].execute(context)
            if chars_val is not None and not isinstance(chars_val, str):
                return NAN
            return operand_val.strip(chars_val)
        return operand_val.strip()

    def _apply_op(self, operand: object) -> str | Sentinel:
        # Not used - execute overridden
        raise NotImplementedError


class LStripOp(StringOp[str | Sentinel]):
    """Strip leading whitespace or chars: str.lstrip(chars)."""

    def __init__(self, operand: OpArgument, chars: OpArgument | None = None) -> None:
        """Initialize lstrip operation."""
        if chars is not None:
            self.children = (cast("Term", operand), cast("Term", chars))
        else:
            self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> str | Sentinel:
        """Execute lstrip operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, str):
            return NAN

        if len(self.children) > 1:
            chars_val = self.children[1].execute(context)
            if chars_val is not None and not isinstance(chars_val, str):
                return NAN
            return operand_val.lstrip(chars_val)
        return operand_val.lstrip()

    def _apply_op(self, operand: object) -> str | Sentinel:
        raise NotImplementedError


class RStripOp(StringOp[str | Sentinel]):
    """Strip trailing whitespace or chars: str.rstrip(chars)."""

    def __init__(self, operand: OpArgument, chars: OpArgument | None = None) -> None:
        """Initialize rstrip operation."""
        if chars is not None:
            self.children = (cast("Term", operand), cast("Term", chars))
        else:
            self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> str | Sentinel:
        """Execute rstrip operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, str):
            return NAN

        if len(self.children) > 1:
            chars_val = self.children[1].execute(context)
            if chars_val is not None and not isinstance(chars_val, str):
                return NAN
            return operand_val.rstrip(chars_val)
        return operand_val.rstrip()

    def _apply_op(self, operand: object) -> str | Sentinel:
        raise NotImplementedError


# =============================================================================
# SPLITTING OPERATIONS
# =============================================================================


class SplitOp(Operation[list[str] | Sentinel]):
    """Split string: str.split(sep, maxsplit)."""

    def __init__(
        self,
        operand: OpArgument,
        sep: OpArgument | None = None,
        maxsplit: int = -1,
    ) -> None:
        """Initialize split operation.

        Args:
            operand: String to split
            sep: Separator (None for whitespace)
            maxsplit: Maximum splits (-1 for unlimited)
        """
        if sep is not None:
            self.children = (cast("Term", operand), cast("Term", sep))
        else:
            self.children = (cast("Term", operand),)
        self._maxsplit = maxsplit

    def execute(self, context: Context) -> list[str] | Sentinel:
        """Execute split operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, str):
            return NAN

        sep_val = None
        if len(self.children) > 1:
            sep_val = self.children[1].execute(context)
            if sep_val is not None and not isinstance(sep_val, str):
                return NAN

        return operand_val.split(sep_val, self._maxsplit)

    def __repr__(self) -> str:
        return f"SplitOp({self.children[0]!r}, maxsplit={self._maxsplit})"


class RSplitOp(Operation[list[str] | Sentinel]):
    """Right split string: str.rsplit(sep, maxsplit)."""

    def __init__(
        self,
        operand: OpArgument,
        sep: OpArgument | None = None,
        maxsplit: int = -1,
    ) -> None:
        """Initialize rsplit operation."""
        if sep is not None:
            self.children = (cast("Term", operand), cast("Term", sep))
        else:
            self.children = (cast("Term", operand),)
        self._maxsplit = maxsplit

    def execute(self, context: Context) -> list[str] | Sentinel:
        """Execute rsplit operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, str):
            return NAN

        sep_val = None
        if len(self.children) > 1:
            sep_val = self.children[1].execute(context)
            if sep_val is not None and not isinstance(sep_val, str):
                return NAN

        return operand_val.rsplit(sep_val, self._maxsplit)

    def __repr__(self) -> str:
        return f"RSplitOp({self.children[0]!r}, maxsplit={self._maxsplit})"


# =============================================================================
# SEARCHING OPERATIONS
# =============================================================================


class FindOp(Operation[int | Sentinel]):
    """Find substring: str.find(sub, start, end)."""

    def __init__(
        self,
        operand: OpArgument,
        sub: OpArgument,
        start: int = 0,
        end: int | None = None,
    ) -> None:
        """Initialize find operation."""
        self.children = (cast("Term", operand), cast("Term", sub))
        self._start = start
        self._end = end

    def execute(self, context: Context) -> int | Sentinel:
        """Execute find operation."""
        operand_val = self.children[0].execute(context)
        sub_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(sub_val, str):
            return NAN

        if self._end is None:
            return operand_val.find(sub_val, self._start)
        return operand_val.find(sub_val, self._start, self._end)

    def __repr__(self) -> str:
        return f"FindOp({self.children[0]!r}, {self.children[1]!r})"


class RFindOp(Operation[int | Sentinel]):
    """Find substring from right: str.rfind(sub, start, end)."""

    def __init__(
        self,
        operand: OpArgument,
        sub: OpArgument,
        start: int = 0,
        end: int | None = None,
    ) -> None:
        """Initialize rfind operation."""
        self.children = (cast("Term", operand), cast("Term", sub))
        self._start = start
        self._end = end

    def execute(self, context: Context) -> int | Sentinel:
        """Execute rfind operation."""
        operand_val = self.children[0].execute(context)
        sub_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(sub_val, str):
            return NAN

        if self._end is None:
            return operand_val.rfind(sub_val, self._start)
        return operand_val.rfind(sub_val, self._start, self._end)

    def __repr__(self) -> str:
        return f"RFindOp({self.children[0]!r}, {self.children[1]!r})"


class CountSubstringOp(Operation[int | Sentinel]):
    """Count substring occurrences: str.count(sub)."""

    def __init__(self, operand: OpArgument, sub: OpArgument) -> None:
        """Initialize count substring operation."""
        self.children = (cast("Term", operand), cast("Term", sub))

    def execute(self, context: Context) -> int | Sentinel:
        """Execute count operation."""
        operand_val = self.children[0].execute(context)
        sub_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(sub_val, str):
            return NAN

        return operand_val.count(sub_val)

    def __repr__(self) -> str:
        return f"CountSubstringOp({self.children[0]!r}, {self.children[1]!r})"


# =============================================================================
# TESTING OPERATIONS
# =============================================================================


class StartsWithOp(Operation[bool | Sentinel]):
    """Check if starts with prefix: str.startswith(prefix)."""

    def __init__(self, operand: OpArgument, prefix: OpArgument) -> None:
        """Initialize startswith operation."""
        self.children = (cast("Term", operand), cast("Term", prefix))

    def execute(self, context: Context) -> bool | Sentinel:
        """Execute startswith operation."""
        operand_val = self.children[0].execute(context)
        prefix_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(prefix_val, str):
            return NAN

        return operand_val.startswith(prefix_val)

    def __repr__(self) -> str:
        return f"StartsWithOp({self.children[0]!r}, {self.children[1]!r})"


class EndsWithOp(Operation[bool | Sentinel]):
    """Check if ends with suffix: str.endswith(suffix)."""

    def __init__(self, operand: OpArgument, suffix: OpArgument) -> None:
        """Initialize endswith operation."""
        self.children = (cast("Term", operand), cast("Term", suffix))

    def execute(self, context: Context) -> bool | Sentinel:
        """Execute endswith operation."""
        operand_val = self.children[0].execute(context)
        suffix_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(suffix_val, str):
            return NAN

        return operand_val.endswith(suffix_val)

    def __repr__(self) -> str:
        return f"EndsWithOp({self.children[0]!r}, {self.children[1]!r})"


class IsDigitOp(StringOp[bool | Sentinel]):
    """Check if all digits: str.isdigit()."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.isdigit()


class IsAlphaOp(StringOp[bool | Sentinel]):
    """Check if all alphabetic: str.isalpha()."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.isalpha()


class IsAlnumOp(StringOp[bool | Sentinel]):
    """Check if alphanumeric: str.isalnum()."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.isalnum()


class IsSpaceOp(StringOp[bool | Sentinel]):
    """Check if all whitespace: str.isspace()."""

    def _apply_op(self, operand: object) -> bool | Sentinel:
        if not isinstance(operand, str):
            return NAN
        return operand.isspace()


# =============================================================================
# PADDING OPERATIONS
# =============================================================================


class CenterOp(Operation[str | Sentinel]):
    """Center in width: str.center(width, fillchar)."""

    def __init__(
        self,
        operand: OpArgument,
        width: OpArgument,
        fillchar: str = " ",
    ) -> None:
        """Initialize center operation."""
        self.children = (cast("Term", operand), cast("Term", width))
        self._fillchar = fillchar

    def execute(self, context: Context) -> str | Sentinel:
        """Execute center operation."""
        operand_val = self.children[0].execute(context)
        width_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(width_val, int):
            return NAN

        return operand_val.center(width_val, self._fillchar)

    def __repr__(self) -> str:
        return f"CenterOp({self.children[0]!r}, {self.children[1]!r})"


class LJustOp(Operation[str | Sentinel]):
    """Left justify: str.ljust(width, fillchar)."""

    def __init__(
        self,
        operand: OpArgument,
        width: OpArgument,
        fillchar: str = " ",
    ) -> None:
        """Initialize ljust operation."""
        self.children = (cast("Term", operand), cast("Term", width))
        self._fillchar = fillchar

    def execute(self, context: Context) -> str | Sentinel:
        """Execute ljust operation."""
        operand_val = self.children[0].execute(context)
        width_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(width_val, int):
            return NAN

        return operand_val.ljust(width_val, self._fillchar)

    def __repr__(self) -> str:
        return f"LJustOp({self.children[0]!r}, {self.children[1]!r})"


class RJustOp(Operation[str | Sentinel]):
    """Right justify: str.rjust(width, fillchar)."""

    def __init__(
        self,
        operand: OpArgument,
        width: OpArgument,
        fillchar: str = " ",
    ) -> None:
        """Initialize rjust operation."""
        self.children = (cast("Term", operand), cast("Term", width))
        self._fillchar = fillchar

    def execute(self, context: Context) -> str | Sentinel:
        """Execute rjust operation."""
        operand_val = self.children[0].execute(context)
        width_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(width_val, int):
            return NAN

        return operand_val.rjust(width_val, self._fillchar)

    def __repr__(self) -> str:
        return f"RJustOp({self.children[0]!r}, {self.children[1]!r})"


class ZFillOp(Operation[str | Sentinel]):
    """Zero-fill: str.zfill(width)."""

    def __init__(self, operand: OpArgument, width: OpArgument) -> None:
        """Initialize zfill operation."""
        self.children = (cast("Term", operand), cast("Term", width))

    def execute(self, context: Context) -> str | Sentinel:
        """Execute zfill operation."""
        operand_val = self.children[0].execute(context)
        width_val = self.children[1].execute(context)

        if not isinstance(operand_val, str) or not isinstance(width_val, int):
            return NAN

        return operand_val.zfill(width_val)

    def __repr__(self) -> str:
        return f"ZFillOp({self.children[0]!r}, {self.children[1]!r})"


# =============================================================================
# REPLACING OPERATIONS
# =============================================================================


class ReplaceOp(Operation[str | Sentinel]):
    """Replace substring: str.replace(old, new, count)."""

    def __init__(
        self,
        operand: OpArgument,
        old: OpArgument,
        new: OpArgument,
        count: int = -1,
    ) -> None:
        """Initialize replace operation."""
        self.children = (
            cast("Term", operand),
            cast("Term", old),
            cast("Term", new),
        )
        self._count = count

    def execute(self, context: Context) -> str | Sentinel:
        """Execute replace operation."""
        operand_val = self.children[0].execute(context)
        old_val = self.children[1].execute(context)
        new_val = self.children[2].execute(context)

        if (
            not isinstance(operand_val, str)
            or not isinstance(old_val, str)
            or not isinstance(new_val, str)
        ):
            return NAN

        if self._count == -1:
            return operand_val.replace(old_val, new_val)
        return operand_val.replace(old_val, new_val, self._count)

    def __repr__(self) -> str:
        return f"ReplaceOp({self.children[0]!r}, {self.children[1]!r}, {self.children[2]!r})"


# =============================================================================
# ENCODING OPERATIONS
# =============================================================================


class EncodeOp(Operation[bytes | Sentinel]):
    """Encode string to bytes: str.encode(encoding)."""

    def __init__(self, operand: OpArgument, encoding: str = "utf-8") -> None:
        """Initialize encode operation."""
        self.children = (cast("Term", operand),)
        self._encoding = encoding

    def execute(self, context: Context) -> bytes | Sentinel:
        """Execute encode operation."""
        operand_val = self.children[0].execute(context)

        if not isinstance(operand_val, str):
            return NAN

        try:
            return operand_val.encode(self._encoding)
        except (UnicodeEncodeError, LookupError):
            return NAN

    def __repr__(self) -> str:
        return f"EncodeOp({self.children[0]!r}, encoding={self._encoding!r})"
