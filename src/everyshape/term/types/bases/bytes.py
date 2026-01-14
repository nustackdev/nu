"""Bytes base classes for Term types.

This module provides bytes-specific operation mixins including:
- BytesMethodsBase - Bytes-specific methods like decode(), hex_(), etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..conversion import literal


if TYPE_CHECKING:
    from ...term import Term
    from ..definitions import BoolType, IntType, ListType, StrType


__all__ = [
    "BytesMethodsBase",
]


class BytesMethodsBase[ResultT]:
    """Base providing bytes-specific methods.

    Methods that return bytes use _wrap_bytes_result() for subclass customization.
    Methods that return str/bool/int use specific types.
    """

    def _wrap_bytes_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    # Decoding
    def decode(self, encoding: str = "utf-8") -> StrType:
        """Decode bytes to string.

        Args:
            encoding: Character encoding

        Returns:
            Decoded string
        """
        from ...comps.typed.bytes import DecodeOp
        from ..definitions import StrType

        return StrType(DecodeOp(self, encoding))

    def hex_(self) -> StrType:
        """Convert to hex string.

        Returns:
            Hex string
        """
        from ...comps.typed.bytes import HexOp
        from ..definitions import StrType

        return StrType(HexOp(self))

    # Case transformation
    def upper(self) -> ResultT:
        """Convert to uppercase.

        Returns:
            Uppercase bytes
        """
        from ...comps.typed.bytes import BytesUpperOp

        return cast("ResultT", self._wrap_bytes_result(BytesUpperOp(self)))

    def lower(self) -> ResultT:
        """Convert to lowercase.

        Returns:
            Lowercase bytes
        """
        from ...comps.typed.bytes import BytesLowerOp

        return cast("ResultT", self._wrap_bytes_result(BytesLowerOp(self)))

    # Stripping
    def strip(self, chars: bytes | Term | None = None) -> ResultT:
        """Strip whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped bytes
        """
        from ...comps.typed.bytes import BytesStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_bytes_result(BytesStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_bytes_result(BytesStripOp(self)))

    def lstrip(self, chars: bytes | Term | None = None) -> ResultT:
        """Strip leading whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped bytes
        """
        from ...comps.typed.bytes import BytesLStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_bytes_result(BytesLStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_bytes_result(BytesLStripOp(self)))

    def rstrip(self, chars: bytes | Term | None = None) -> ResultT:
        """Strip trailing whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped bytes
        """
        from ...comps.typed.bytes import BytesRStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_bytes_result(BytesRStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_bytes_result(BytesRStripOp(self)))

    # Splitting
    def split_bytes(self, sep: bytes | Term | None = None, maxsplit: int = -1) -> ListType[bytes]:
        """Split bytes.

        Args:
            sep: Separator (None for whitespace)
            maxsplit: Maximum splits (-1 for unlimited)

        Returns:
            List of bytes
        """
        from ...comps.typed.bytes import BytesSplitOp
        from ..definitions import ListType

        if sep is not None:
            return ListType(BytesSplitOp(self, literal(sep), maxsplit))
        return ListType(BytesSplitOp(self, None, maxsplit))

    # Searching
    def find_bytes(self, sub: bytes | Term, start: int = 0, end: int | None = None) -> IntType:
        """Find sub-bytes.

        Args:
            sub: Sub-bytes to find
            start: Start index
            end: End index

        Returns:
            Index or -1 if not found
        """
        from ...comps.typed.bytes import BytesFindOp
        from ..definitions import IntType

        return IntType(BytesFindOp(self, literal(sub), start, end))

    def count_bytes(self, sub: bytes | Term) -> IntType:
        """Count sub-bytes occurrences.

        Args:
            sub: Sub-bytes to count

        Returns:
            Count
        """
        from ...comps.typed.bytes import BytesCountOp
        from ..definitions import IntType

        return IntType(BytesCountOp(self, literal(sub)))

    # Testing
    def startswith(self, prefix: bytes | Term) -> BoolType:
        """Check if starts with prefix.

        Args:
            prefix: Prefix to check

        Returns:
            Boolean result
        """
        from ...comps.typed.bytes import BytesStartsWithOp
        from ..definitions import BoolType

        return BoolType(BytesStartsWithOp(self, literal(prefix)))

    def endswith(self, suffix: bytes | Term) -> BoolType:
        """Check if ends with suffix.

        Args:
            suffix: Suffix to check

        Returns:
            Boolean result
        """
        from ...comps.typed.bytes import BytesEndsWithOp
        from ..definitions import BoolType

        return BoolType(BytesEndsWithOp(self, literal(suffix)))

    # Replacing
    def replace(self, old: bytes | Term, new: bytes | Term, count: int = -1) -> ResultT:
        """Replace sub-bytes.

        Args:
            old: Bytes to replace
            new: Replacement bytes
            count: Maximum replacements (-1 for all)

        Returns:
            Modified bytes
        """
        from ...comps.typed.bytes import BytesReplaceOp

        return cast(
            "ResultT",
            self._wrap_bytes_result(BytesReplaceOp(self, literal(old), literal(new), count)),
        )
