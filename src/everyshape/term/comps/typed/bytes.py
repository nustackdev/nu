"""Bytes operations for Term expressions.

This module provides type-safe operations on bytes Terms:

Decoding: DecodeOp, HexOp
Case transformation: BytesUpperOp, BytesLowerOp
Stripping: BytesStripOp, BytesLStripOp, BytesRStripOp
Splitting: BytesSplitOp
Searching: BytesFindOp, BytesCountOp
Testing: BytesStartsWithOp, BytesEndsWithOp
Replacing: BytesReplaceOp

Design principles:
1. Atomic classes: one operation = one class
2. Runtime type checking: validate input is bytes at execution
3. Special value propagation: Empty/NaN flow through operations
4. Type safety: preserve return types

Usage:
    # Direct instantiation
    DecodeOp(data.get())
    BytesSplitOp(data.get(), b",")

    # Via ergonomics mixin
    data.get().decode()
    data.get().split(b",")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.typing import NAN, Sentinel

from ...term import Operation


if TYPE_CHECKING:
    from ...context import Context
    from ...term import Term
    from ...types.bases import UnionBaseType

__all__ = [
    "BytesCountOp",
    "BytesEndsWithOp",
    "BytesFindOp",
    "BytesLStripOp",
    "BytesLowerOp",
    "BytesRStripOp",
    "BytesReplaceOp",
    "BytesSplitOp",
    "BytesStartsWithOp",
    "BytesStripOp",
    "BytesUpperOp",
    "DecodeOp",
    "HexOp",
]


# =============================================================================
# ABSTRACT BYTES OPERATION
# =============================================================================


type OpArgument = Term | UnionBaseType


class BytesOp[ResultT](Operation[ResultT]):
    """Base class for bytes operations.

    Defines execution pattern: evaluate operand → validate bytes →
    apply operation → return result.
    """

    def __init__(self, operand: OpArgument) -> None:
        """Initialize bytes operation.

        Args:
            operand: Term that should produce bytes
        """
        self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> ResultT:
        """Execute bytes operation.

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
            operand: The evaluated bytes

        Returns:
            Operation result
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r})"


# =============================================================================
# DECODING OPERATIONS
# =============================================================================


class DecodeOp(BytesOp[str | Sentinel]):
    """Decode bytes to string: bytes.decode(encoding)."""

    def __init__(self, operand: OpArgument, encoding: str = "utf-8") -> None:
        """Initialize decode operation.

        Args:
            operand: Bytes to decode
            encoding: Character encoding
        """
        super().__init__(operand)
        self._encoding = encoding

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, bytes):
            return NAN
        try:
            return operand.decode(self._encoding)
        except (UnicodeDecodeError, LookupError):
            return NAN

    def __repr__(self) -> str:
        return f"DecodeOp({self.children[0]!r}, encoding={self._encoding!r})"


class HexOp(BytesOp[str | Sentinel]):
    """Convert to hex string: bytes.hex()."""

    def _apply_op(self, operand: object) -> str | Sentinel:
        if not isinstance(operand, bytes):
            return NAN
        return operand.hex()


# =============================================================================
# CASE TRANSFORMATION OPERATIONS
# =============================================================================


class BytesUpperOp(BytesOp[bytes | Sentinel]):
    """Convert to uppercase: bytes.upper()."""

    def _apply_op(self, operand: object) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return NAN
        return operand.upper()


class BytesLowerOp(BytesOp[bytes | Sentinel]):
    """Convert to lowercase: bytes.lower()."""

    def _apply_op(self, operand: object) -> bytes | Sentinel:
        if not isinstance(operand, bytes):
            return NAN
        return operand.lower()


# =============================================================================
# STRIPPING OPERATIONS
# =============================================================================


class BytesStripOp(BytesOp[bytes | Sentinel]):
    """Strip bytes: bytes.strip(chars)."""

    def __init__(self, operand: OpArgument, chars: OpArgument | None = None) -> None:
        """Initialize strip operation.

        Args:
            operand: Bytes to strip
            chars: Bytes to strip (None for whitespace)
        """
        if chars is not None:
            self.children = (cast("Term", operand), cast("Term", chars))
        else:
            self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> bytes | Sentinel:
        """Execute strip operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, bytes):
            return NAN

        if len(self.children) > 1:
            chars_val = self.children[1].execute(context)
            if chars_val is not None and not isinstance(chars_val, bytes):
                return NAN
            return operand_val.strip(chars_val)
        return operand_val.strip()

    def _apply_op(self, operand: object) -> bytes | Sentinel:
        raise NotImplementedError


class BytesLStripOp(BytesOp[bytes | Sentinel]):
    """Strip leading bytes: bytes.lstrip(chars)."""

    def __init__(self, operand: OpArgument, chars: OpArgument | None = None) -> None:
        """Initialize lstrip operation."""
        if chars is not None:
            self.children = (cast("Term", operand), cast("Term", chars))
        else:
            self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> bytes | Sentinel:
        """Execute lstrip operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, bytes):
            return NAN

        if len(self.children) > 1:
            chars_val = self.children[1].execute(context)
            if chars_val is not None and not isinstance(chars_val, bytes):
                return NAN
            return operand_val.lstrip(chars_val)
        return operand_val.lstrip()

    def _apply_op(self, operand: object) -> bytes | Sentinel:
        raise NotImplementedError


class BytesRStripOp(BytesOp[bytes | Sentinel]):
    """Strip trailing bytes: bytes.rstrip(chars)."""

    def __init__(self, operand: OpArgument, chars: OpArgument | None = None) -> None:
        """Initialize rstrip operation."""
        if chars is not None:
            self.children = (cast("Term", operand), cast("Term", chars))
        else:
            self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> bytes | Sentinel:
        """Execute rstrip operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, bytes):
            return NAN

        if len(self.children) > 1:
            chars_val = self.children[1].execute(context)
            if chars_val is not None and not isinstance(chars_val, bytes):
                return NAN
            return operand_val.rstrip(chars_val)
        return operand_val.rstrip()

    def _apply_op(self, operand: object) -> bytes | Sentinel:
        raise NotImplementedError


# =============================================================================
# SPLITTING OPERATIONS
# =============================================================================


class BytesSplitOp(Operation[list[bytes] | Sentinel]):
    """Split bytes: bytes.split(sep, maxsplit)."""

    def __init__(
        self,
        operand: OpArgument,
        sep: OpArgument | None = None,
        maxsplit: int = -1,
    ) -> None:
        """Initialize split operation.

        Args:
            operand: Bytes to split
            sep: Separator (None for whitespace)
            maxsplit: Maximum splits (-1 for unlimited)
        """
        if sep is not None:
            self.children = (cast("Term", operand), cast("Term", sep))
        else:
            self.children = (cast("Term", operand),)
        self._maxsplit = maxsplit

    def execute(self, context: Context) -> list[bytes] | Sentinel:
        """Execute split operation."""
        operand_val = self.children[0].execute(context)
        if not isinstance(operand_val, bytes):
            return NAN

        sep_val = None
        if len(self.children) > 1:
            sep_val = self.children[1].execute(context)
            if sep_val is not None and not isinstance(sep_val, bytes):
                return NAN

        return operand_val.split(sep_val, self._maxsplit)

    def __repr__(self) -> str:
        return f"BytesSplitOp({self.children[0]!r}, maxsplit={self._maxsplit})"


# =============================================================================
# SEARCHING OPERATIONS
# =============================================================================


class BytesFindOp(Operation[int | Sentinel]):
    """Find sub-bytes: bytes.find(sub, start, end)."""

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

        if not isinstance(operand_val, bytes) or not isinstance(sub_val, bytes):
            return NAN

        if self._end is None:
            return operand_val.find(sub_val, self._start)
        return operand_val.find(sub_val, self._start, self._end)

    def __repr__(self) -> str:
        return f"BytesFindOp({self.children[0]!r}, {self.children[1]!r})"


class BytesCountOp(Operation[int | Sentinel]):
    """Count sub-bytes occurrences: bytes.count(sub)."""

    def __init__(self, operand: OpArgument, sub: OpArgument) -> None:
        """Initialize count operation."""
        self.children = (cast("Term", operand), cast("Term", sub))

    def execute(self, context: Context) -> int | Sentinel:
        """Execute count operation."""
        operand_val = self.children[0].execute(context)
        sub_val = self.children[1].execute(context)

        if not isinstance(operand_val, bytes) or not isinstance(sub_val, bytes):
            return NAN

        return operand_val.count(sub_val)

    def __repr__(self) -> str:
        return f"BytesCountOp({self.children[0]!r}, {self.children[1]!r})"


# =============================================================================
# TESTING OPERATIONS
# =============================================================================


class BytesStartsWithOp(Operation[bool | Sentinel]):
    """Check if starts with prefix: bytes.startswith(prefix)."""

    def __init__(self, operand: OpArgument, prefix: OpArgument) -> None:
        """Initialize startswith operation."""
        self.children = (cast("Term", operand), cast("Term", prefix))

    def execute(self, context: Context) -> bool | Sentinel:
        """Execute startswith operation."""
        operand_val = self.children[0].execute(context)
        prefix_val = self.children[1].execute(context)

        if not isinstance(operand_val, bytes) or not isinstance(prefix_val, bytes):
            return NAN

        return operand_val.startswith(prefix_val)

    def __repr__(self) -> str:
        return f"BytesStartsWithOp({self.children[0]!r}, {self.children[1]!r})"


class BytesEndsWithOp(Operation[bool | Sentinel]):
    """Check if ends with suffix: bytes.endswith(suffix)."""

    def __init__(self, operand: OpArgument, suffix: OpArgument) -> None:
        """Initialize endswith operation."""
        self.children = (cast("Term", operand), cast("Term", suffix))

    def execute(self, context: Context) -> bool | Sentinel:
        """Execute endswith operation."""
        operand_val = self.children[0].execute(context)
        suffix_val = self.children[1].execute(context)

        if not isinstance(operand_val, bytes) or not isinstance(suffix_val, bytes):
            return NAN

        return operand_val.endswith(suffix_val)

    def __repr__(self) -> str:
        return f"BytesEndsWithOp({self.children[0]!r}, {self.children[1]!r})"


# =============================================================================
# REPLACING OPERATIONS
# =============================================================================


class BytesReplaceOp(Operation[bytes | Sentinel]):
    """Replace sub-bytes: bytes.replace(old, new, count)."""

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

    def execute(self, context: Context) -> bytes | Sentinel:
        """Execute replace operation."""
        operand_val = self.children[0].execute(context)
        old_val = self.children[1].execute(context)
        new_val = self.children[2].execute(context)

        if (
            not isinstance(operand_val, bytes)
            or not isinstance(old_val, bytes)
            or not isinstance(new_val, bytes)
        ):
            return NAN

        if self._count == -1:
            return operand_val.replace(old_val, new_val)
        return operand_val.replace(old_val, new_val, self._count)

    def __repr__(self) -> str:
        return f"BytesReplaceOp({self.children[0]!r}, {self.children[1]!r}, {self.children[2]!r})"
