"""Bytes types for Term expressions.

This module provides BytesType including all bytes-specific methods.
BytesMethodsBase is merged directly into BytesType.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast, overload

from everyshape.term.conversion import literal

from ..bases import (
    ComparisonBase,
    ContainableBase,
    LengthableBase,
    LogicalBase,
    SliceableBase,
    Type,
)


if TYPE_CHECKING:
    from everyshape.term.term import Term

    from ..bool.type import BoolType
    from ..int.type import IntType
    from ..list.type import ListType
    from ..str.type import StrType


__all__ = [
    "BytesType",
]


class BytesType(
    LengthableBase,
    SliceableBase["BytesType"],
    ContainableBase["int | bytes"],
    ComparisonBase["bytes | BytesType"],
    LogicalBase["bytes | BytesType", "BoolType"],
    Type[bytes],
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
        from ..bool.type import BoolType

        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from ..bool.type import BoolType

        return BoolType(operand)

    def _wrap_bytes_result(self, operand: Term) -> Term:
        return BytesType(operand)

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        return BytesType(operand)

    def __add__(self, other: bytes | BytesType) -> BytesType:
        from everyshape.ops import AddOp

        return BytesType(AddOp(self, literal(other)))

    def __radd__(self, other: bytes) -> BytesType:
        from everyshape.ops import AddOp

        return BytesType(AddOp(literal(other), self))

    @overload
    def __getitem__(self, key: int) -> IntType: ...
    @overload
    def __getitem__(self, key: slice) -> BytesType: ...
    def __getitem__(self, key: int | slice) -> BytesType | IntType:
        from everyshape.ops import AtOp, SliceOp

        from ..int.type import IntType

        if isinstance(key, slice):
            return BytesType(SliceOp[bytes](self, key.start, key.stop, key.step))
        return IntType(AtOp[int](self, literal(key)))

    # =========================================================================
    # BYTES-SPECIFIC METHODS (merged from BytesMethodsBase)
    # =========================================================================

    # Decoding
    def decode(self, encoding: str = "utf-8") -> StrType:
        """Decode bytes to string."""
        from everyshape.types.bytes.ops import DecodeOp

        from ..str.type import StrType

        return StrType(DecodeOp(self, encoding))

    def hex_(self) -> StrType:
        """Convert to hex string."""
        from everyshape.types.bytes.ops import HexOp

        from ..str.type import StrType

        return StrType(HexOp(self))

    # Case transformation
    def upper(self) -> BytesType:
        """Convert to uppercase."""
        from everyshape.types.bytes.ops import BytesUpperOp

        return cast("BytesType", self._wrap_bytes_result(BytesUpperOp(self)))

    def lower(self) -> BytesType:
        """Convert to lowercase."""
        from everyshape.types.bytes.ops import BytesLowerOp

        return cast("BytesType", self._wrap_bytes_result(BytesLowerOp(self)))

    # Stripping
    def strip(self, chars: bytes | Term | None = None) -> BytesType:
        """Strip whitespace or chars."""
        from everyshape.types.bytes.ops import BytesStripOp

        if chars is not None:
            return cast("BytesType", self._wrap_bytes_result(BytesStripOp(self, literal(chars))))
        return cast("BytesType", self._wrap_bytes_result(BytesStripOp(self)))

    def lstrip(self, chars: bytes | Term | None = None) -> BytesType:
        """Strip leading whitespace or chars."""
        from everyshape.types.bytes.ops import BytesLStripOp

        if chars is not None:
            return cast("BytesType", self._wrap_bytes_result(BytesLStripOp(self, literal(chars))))
        return cast("BytesType", self._wrap_bytes_result(BytesLStripOp(self)))

    def rstrip(self, chars: bytes | Term | None = None) -> BytesType:
        """Strip trailing whitespace or chars."""
        from everyshape.types.bytes.ops import BytesRStripOp

        if chars is not None:
            return cast("BytesType", self._wrap_bytes_result(BytesRStripOp(self, literal(chars))))
        return cast("BytesType", self._wrap_bytes_result(BytesRStripOp(self)))

    # Splitting
    def split_bytes(self, sep: bytes | Term | None = None, maxsplit: int = -1) -> ListType[bytes]:
        """Split bytes."""
        from everyshape.types.bytes.ops import BytesSplitOp

        from ..list.type import ListType

        if sep is not None:
            return ListType(BytesSplitOp(self, literal(sep), maxsplit))
        return ListType(BytesSplitOp(self, None, maxsplit))

    # Searching
    def find_bytes(self, sub: bytes | Term, start: int = 0, end: int | None = None) -> IntType:
        """Find sub-bytes."""
        from everyshape.types.bytes.ops import BytesFindOp

        from ..int.type import IntType

        return IntType(BytesFindOp(self, literal(sub), start, end))

    def count_bytes(self, sub: bytes | Term) -> IntType:
        """Count sub-bytes occurrences."""
        from everyshape.types.bytes.ops import BytesCountOp

        from ..int.type import IntType

        return IntType(BytesCountOp(self, literal(sub)))

    # Testing
    def startswith(self, prefix: bytes | Term) -> BoolType:
        """Check if starts with prefix."""
        from everyshape.types.bytes.ops import BytesStartsWithOp

        from ..bool.type import BoolType

        return BoolType(BytesStartsWithOp(self, literal(prefix)))

    def endswith(self, suffix: bytes | Term) -> BoolType:
        """Check if ends with suffix."""
        from everyshape.types.bytes.ops import BytesEndsWithOp

        from ..bool.type import BoolType

        return BoolType(BytesEndsWithOp(self, literal(suffix)))

    # Replacing
    def replace(self, old: bytes | Term, new: bytes | Term, count: int = -1) -> BytesType:
        """Replace sub-bytes."""
        from everyshape.types.bytes.ops import BytesReplaceOp

        return cast(
            "BytesType",
            self._wrap_bytes_result(BytesReplaceOp(self, literal(old), literal(new), count)),
        )
