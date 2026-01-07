"""Bytes base classes for RValue types.

This module provides bytes-specific operation mixins including:
- BytesMethodsBase - Bytes-specific methods like decode(), hex_(), etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..conversion import literal


if TYPE_CHECKING:
    from ...term import RValue
    from ..values import BoolValue, IntValue, ListValue, StrValue


__all__ = [
    "BytesMethodsBase",
]


class BytesMethodsBase[ResultT]:
    """Base providing bytes-specific methods.

    Methods that return bytes use _wrap_bytes_result() for subclass customization.
    Methods that return str/bool/int use specific types.
    """

    def _wrap_bytes_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    # Decoding
    def decode(self, encoding: str = "utf-8") -> StrValue:
        """Decode bytes to string.

        Args:
            encoding: Character encoding

        Returns:
            Decoded string
        """
        from ...comps.types.bytes import DecodeOp
        from ..values import StrValue

        return StrValue(DecodeOp(self, encoding))

    def hex_(self) -> StrValue:
        """Convert to hex string.

        Returns:
            Hex string
        """
        from ...comps.types.bytes import HexOp
        from ..values import StrValue

        return StrValue(HexOp(self))

    # Case transformation
    def upper(self) -> ResultT:
        """Convert to uppercase.

        Returns:
            Uppercase bytes
        """
        from ...comps.types.bytes import BytesUpperOp

        return cast("ResultT", self._wrap_bytes_result(BytesUpperOp(self)))

    def lower(self) -> ResultT:
        """Convert to lowercase.

        Returns:
            Lowercase bytes
        """
        from ...comps.types.bytes import BytesLowerOp

        return cast("ResultT", self._wrap_bytes_result(BytesLowerOp(self)))

    # Stripping
    def strip(self, chars: bytes | RValue | None = None) -> ResultT:
        """Strip whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped bytes
        """
        from ...comps.types.bytes import BytesStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_bytes_result(BytesStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_bytes_result(BytesStripOp(self)))

    def lstrip(self, chars: bytes | RValue | None = None) -> ResultT:
        """Strip leading whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped bytes
        """
        from ...comps.types.bytes import BytesLStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_bytes_result(BytesLStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_bytes_result(BytesLStripOp(self)))

    def rstrip(self, chars: bytes | RValue | None = None) -> ResultT:
        """Strip trailing whitespace or chars.

        Args:
            chars: Characters to strip (None for whitespace)

        Returns:
            Stripped bytes
        """
        from ...comps.types.bytes import BytesRStripOp

        if chars is not None:
            return cast("ResultT", self._wrap_bytes_result(BytesRStripOp(self, literal(chars))))
        return cast("ResultT", self._wrap_bytes_result(BytesRStripOp(self)))

    # Splitting
    def split_bytes(
        self, sep: bytes | RValue | None = None, maxsplit: int = -1
    ) -> ListValue[bytes]:
        """Split bytes.

        Args:
            sep: Separator (None for whitespace)
            maxsplit: Maximum splits (-1 for unlimited)

        Returns:
            List of bytes
        """
        from ...comps.types.bytes import BytesSplitOp
        from ..values import ListValue

        if sep is not None:
            return ListValue(BytesSplitOp(self, literal(sep), maxsplit))
        return ListValue(BytesSplitOp(self, None, maxsplit))

    # Searching
    def find_bytes(self, sub: bytes | RValue, start: int = 0, end: int | None = None) -> IntValue:
        """Find sub-bytes.

        Args:
            sub: Sub-bytes to find
            start: Start index
            end: End index

        Returns:
            Index or -1 if not found
        """
        from ...comps.types.bytes import BytesFindOp
        from ..values import IntValue

        return IntValue(BytesFindOp(self, literal(sub), start, end))

    def count_bytes(self, sub: bytes | RValue) -> IntValue:
        """Count sub-bytes occurrences.

        Args:
            sub: Sub-bytes to count

        Returns:
            Count
        """
        from ...comps.types.bytes import BytesCountOp
        from ..values import IntValue

        return IntValue(BytesCountOp(self, literal(sub)))

    # Testing
    def startswith(self, prefix: bytes | RValue) -> BoolValue:
        """Check if starts with prefix.

        Args:
            prefix: Prefix to check

        Returns:
            Boolean result
        """
        from ...comps.types.bytes import BytesStartsWithOp
        from ..values import BoolValue

        return BoolValue(BytesStartsWithOp(self, literal(prefix)))

    def endswith(self, suffix: bytes | RValue) -> BoolValue:
        """Check if ends with suffix.

        Args:
            suffix: Suffix to check

        Returns:
            Boolean result
        """
        from ...comps.types.bytes import BytesEndsWithOp
        from ..values import BoolValue

        return BoolValue(BytesEndsWithOp(self, literal(suffix)))

    # Replacing
    def replace(self, old: bytes | RValue, new: bytes | RValue, count: int = -1) -> ResultT:
        """Replace sub-bytes.

        Args:
            old: Bytes to replace
            new: Replacement bytes
            count: Maximum replacements (-1 for all)

        Returns:
            Modified bytes
        """
        from ...comps.types.bytes import BytesReplaceOp

        return cast(
            "ResultT",
            self._wrap_bytes_result(BytesReplaceOp(self, literal(old), literal(new), count)),
        )
