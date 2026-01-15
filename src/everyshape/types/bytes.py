"""Bytes types for Term expressions.

This module provides BytesType including all bytes-specific methods.
BytesMethodsBase is merged directly into BytesType.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast, overload

from .bases import (
    BaseType,
    ComparisonBase,
    ContainableBase,
    LengthableBase,
    LogicalBase,
    SliceableBase,
)


if TYPE_CHECKING:
    from everyshape.term import BytesArg, IntArg, StrArg, Term

    from .bool import BoolType
    from .int import IntType
    from .list import ListType
    from .str import StrType


__all__ = [
    "BytesType",
]


class BytesType(
    LengthableBase,
    SliceableBase["BytesType"],
    ContainableBase["int | bytes"],
    ComparisonBase["bytes | BytesType"],
    LogicalBase["bytes | BytesType", "BoolType"],
    BaseType[bytes],
):
    """Bytes type - represents bytes expressions (literal or computed).

    Supports concatenation, bytes operations, comparison, and logical operations.

    Example:
        >>> x = BytesType(b"hello")
        >>> y = x + b" world"  # Returns BytesType
        >>> z = x.decode()  # Returns StrType
    """

    VALUE_TYPE: ClassVar[type] = bytes

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_bytes_result(self, operand: Term) -> Term:
        return BytesType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        return BytesType(operand)

    def __add__(self, other: bytes | BytesType) -> BytesType:
        from everyshape.ops import AddOp

        return BytesType(AddOp(self, other))

    def __radd__(self, other: bytes) -> BytesType:
        from everyshape.ops import AddOp

        return BytesType(AddOp(other, self))

    @overload
    def __getitem__(self, key: int) -> IntType: ...
    @overload
    def __getitem__(self, key: slice) -> BytesType: ...
    def __getitem__(self, key: int | slice) -> BytesType | IntType:
        from everyshape.ops import AtOp, SliceOp

        from .int import IntType

        if isinstance(key, slice):
            return BytesType(SliceOp[bytes](self, key.start, key.stop, key.step))
        return IntType(AtOp[int](self, key))

    # =========================================================================
    # BYTES-SPECIFIC METHODS (merged from BytesMethodsBase)
    # =========================================================================

    # Decoding
    def decode(self, encoding: StrArg = "utf-8") -> StrType:
        """Decode bytes to string."""
        from .bytes_ops import DecodeOp
        from .str import StrType

        return StrType(DecodeOp(self, encoding))

    def hex_(self) -> StrType:
        """Convert to hex string."""
        from .bytes_ops import HexOp
        from .str import StrType

        return StrType(HexOp(self))

    # Case transformation
    def upper(self) -> BytesType:
        """Convert to uppercase."""
        from .bytes_ops import BytesUpperOp

        return cast("BytesType", self._wrap_bytes_result(BytesUpperOp(self)))

    def lower(self) -> BytesType:
        """Convert to lowercase."""
        from .bytes_ops import BytesLowerOp

        return cast("BytesType", self._wrap_bytes_result(BytesLowerOp(self)))

    # Stripping
    def strip(self, chars: BytesArg | None = None) -> BytesType:
        """Strip whitespace or chars."""
        from .bytes_ops import BytesStripOp

        if chars is not None:
            return cast("BytesType", self._wrap_bytes_result(BytesStripOp(self, chars)))
        return cast("BytesType", self._wrap_bytes_result(BytesStripOp(self)))

    def lstrip(self, chars: BytesArg | None = None) -> BytesType:
        """Strip leading whitespace or chars."""
        from .bytes_ops import BytesLStripOp

        if chars is not None:
            return cast("BytesType", self._wrap_bytes_result(BytesLStripOp(self, chars)))
        return cast("BytesType", self._wrap_bytes_result(BytesLStripOp(self)))

    def rstrip(self, chars: BytesArg | None = None) -> BytesType:
        """Strip trailing whitespace or chars."""
        from .bytes_ops import BytesRStripOp

        if chars is not None:
            return cast("BytesType", self._wrap_bytes_result(BytesRStripOp(self, chars)))
        return cast("BytesType", self._wrap_bytes_result(BytesRStripOp(self)))

    # Splitting
    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListType[bytes]:
        """Split bytes."""
        from .bytes_ops import BytesSplitOp
        from .list import ListType

        if sep is not None:
            return ListType(BytesSplitOp(self, sep, maxsplit))
        return ListType(BytesSplitOp(self, None, maxsplit))

    # Searching
    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntType:
        """Find sub-bytes."""
        from .bytes_ops import BytesFindOp
        from .int import IntType

        return IntType(BytesFindOp(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> IntType:
        """Count sub-bytes occurrences."""
        from .bytes_ops import BytesCountOp
        from .int import IntType

        return IntType(BytesCountOp(self, sub))

    # Testing
    def startswith(self, prefix: BytesArg) -> BoolType:
        """Check if starts with prefix."""
        from .bool import BoolType
        from .bytes_ops import BytesStartsWithOp

        return BoolType(BytesStartsWithOp(self, prefix))

    def endswith(self, suffix: BytesArg) -> BoolType:
        """Check if ends with suffix."""
        from .bool import BoolType
        from .bytes_ops import BytesEndsWithOp

        return BoolType(BytesEndsWithOp(self, suffix))

    # Replacing
    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> BytesType:
        """Replace sub-bytes."""
        from .bytes_ops import BytesReplaceOp

        return cast(
            "BytesType",
            self._wrap_bytes_result(BytesReplaceOp(self, old, new, count)),
        )
