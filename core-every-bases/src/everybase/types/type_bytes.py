"""Bytes ref base combining sequence traits.

BytesType = TypeBase[bytes] + Lengthable + Sliceable + Containable + Comparable + Logical

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload

from everybase.capabilities import (
    ComparableBase,
    ContainableBase,
    LengthableBase,
    LogicalBase,
    SliceableBase,
)

from .base import TypeBase


if TYPE_CHECKING:
    from everyabc import BytesArg, IntArg, StrArg, Term
    from everybase.values import BoolValue, BytesValue, IntValue, ListValue, StrValue


__all__ = [
    "BytesType",
]


class BytesType(
    LengthableBase,
    SliceableBase["BytesValue"],
    ContainableBase["int | bytes"],
    ComparableBase["bytes | BytesValue"],
    LogicalBase["bytes | BytesValue", "BoolValue"],
    TypeBase[bytes],
):
    """Abstract base for bytes refs.

    Combines sequence and comparison traits, returns concrete py types.
    """

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_bytes_result(self, operand: Term) -> BytesValue:
        from everybase.values import BytesValue

        return BytesValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> BytesValue:
        from everybase.values import BytesValue

        return BytesValue(operand)

    def __add__(self, other: bytes | BytesType) -> BytesValue:
        from everybase.morphisms import AddOp
        from everybase.values import BytesValue

        return BytesValue(AddOp(self, other))

    def __radd__(self, other: bytes) -> BytesValue:
        from everybase.morphisms import AddOp
        from everybase.values import BytesValue

        return BytesValue(AddOp(other, self))

    @overload
    def __getitem__(self, key: int) -> IntValue: ...
    @overload
    def __getitem__(self, key: slice) -> BytesValue: ...
    def __getitem__(self, key: int | slice) -> BytesValue | IntValue:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.values import BytesValue, IntValue

        if isinstance(key, slice):
            return BytesValue(SliceOp(self, key.start, key.stop, key.step))
        return IntValue(AtOp(self, key))

    # =========================================================================
    # BYTES-SPECIFIC METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> StrValue:
        """Decode bytes to string."""
        from everybase.morphisms.type_bytes import DecodeOp
        from everybase.values import StrValue

        return StrValue(DecodeOp(self, encoding))

    def hex_(self) -> StrValue:
        """Convert to hex string."""
        from everybase.morphisms.type_bytes import HexOp
        from everybase.values import StrValue

        return StrValue(HexOp(self))

    def upper(self) -> BytesValue:
        """Convert to uppercase."""
        from everybase.morphisms.type_bytes import BytesUpperOp

        return cast("BytesValue", self._wrap_bytes_result(BytesUpperOp(self)))

    def lower(self) -> BytesValue:
        """Convert to lowercase."""
        from everybase.morphisms.type_bytes import BytesLowerOp

        return cast("BytesValue", self._wrap_bytes_result(BytesLowerOp(self)))

    def strip(self, chars: BytesArg | None = None) -> BytesValue:
        """Strip whitespace or chars."""
        from everybase.morphisms.type_bytes import BytesStripOp

        return cast("BytesValue", self._wrap_bytes_result(BytesStripOp(self, chars)))

    def lstrip(self, chars: BytesArg | None = None) -> BytesValue:
        """Strip leading whitespace or chars."""
        from everybase.morphisms.type_bytes import BytesLStripOp

        return cast("BytesValue", self._wrap_bytes_result(BytesLStripOp(self, chars)))

    def rstrip(self, chars: BytesArg | None = None) -> BytesValue:
        """Strip trailing whitespace or chars."""
        from everybase.morphisms.type_bytes import BytesRStripOp

        return cast("BytesValue", self._wrap_bytes_result(BytesRStripOp(self, chars)))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListValue[bytes]:
        """Split bytes."""
        from everybase.morphisms.type_bytes import BytesSplitOp
        from everybase.values import ListValue

        if sep is not None:
            return ListValue(BytesSplitOp(self, sep, maxsplit))
        return ListValue(BytesSplitOp(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntValue:
        """Find sub-bytes."""
        from everybase.morphisms.type_bytes import BytesFindOp
        from everybase.values import IntValue

        return IntValue(BytesFindOp(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> IntValue:
        """Count sub-bytes occurrences."""
        from everybase.morphisms.type_bytes import BytesCountOp
        from everybase.values import IntValue

        return IntValue(BytesCountOp(self, sub))

    def startswith(self, prefix: BytesArg) -> BoolValue:
        """Check if starts with prefix."""
        from everybase.morphisms.type_bytes import BytesStartsWithOp
        from everybase.values import BoolValue

        return BoolValue(BytesStartsWithOp(self, prefix))

    def endswith(self, suffix: BytesArg) -> BoolValue:
        """Check if ends with suffix."""
        from everybase.morphisms.type_bytes import BytesEndsWithOp
        from everybase.values import BoolValue

        return BoolValue(BytesEndsWithOp(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> BytesValue:
        """Replace sub-bytes."""
        from everybase.morphisms.type_bytes import BytesReplaceOp

        return cast("BytesValue", self._wrap_bytes_result(BytesReplaceOp(self, old, new, count)))
