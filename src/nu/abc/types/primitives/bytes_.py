"""Bytes ref base combining sequence traits.

BytesType = Object[bytes] + Sliceable + Comparable + Logical

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload

from ...capabilities import (
    ComparableBase,
    LogicalBase,
    SliceableBase,
)
from ..object import Object


if TYPE_CHECKING:
    from nu.core import BytesArg, IntArg, StrArg, Term

    from ...values import BoolValue, BytesValue, IntValue, ListValue, StrValue


__all__ = [
    "BytesType",
]


class BytesType(
    SliceableBase["BytesValue"],
    ComparableBase["BytesArg"],
    LogicalBase["BytesArg", "BoolValue"],
    Object[bytes],
):
    """Abstract base for bytes refs.

    Combines sequence and comparison traits, returns concrete py types.
    """

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def _wrap_bytes_result(self, operand: Term) -> BytesValue:
        from ...values import BytesValue

        return BytesValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> BytesValue:
        from ...values import BytesValue

        return BytesValue(operand)

    def __add__(self, other: BytesArg) -> BytesValue:
        from ...morphisms import AddOp
        from ...values import BytesValue

        return BytesValue(AddOp(self, other))

    def __radd__(self, other: BytesArg) -> BytesValue:
        from ...morphisms import AddOp
        from ...values import BytesValue

        return BytesValue(AddOp(other, self))

    @overload
    def __getitem__(self, key: IntArg) -> IntValue: ...
    @overload
    def __getitem__(self, key: slice) -> BytesValue: ...
    def __getitem__(self, key: IntArg | slice) -> BytesValue | IntValue:
        from ...morphisms import AtOp, SliceOp
        from ...values import BytesValue, IntValue

        if isinstance(key, slice):
            return BytesValue(SliceOp(self, key.start, key.stop, key.step))
        return IntValue(AtOp(self, key))

    # =========================================================================
    # BYTES-SPECIFIC METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> StrValue:
        """Decode bytes to string."""
        from ...morphisms.bytes_ import DecodeOp
        from ...values import StrValue

        return StrValue(DecodeOp(self, encoding))

    def hex_(self) -> StrValue:
        """Convert to hex string."""
        from ...morphisms.bytes_ import HexOp
        from ...values import StrValue

        return StrValue(HexOp(self))

    def upper(self) -> BytesValue:
        """Convert to uppercase."""
        from ...morphisms.bytes_ import BytesUpperOp

        return cast("BytesValue", self._wrap_bytes_result(BytesUpperOp(self)))

    def lower(self) -> BytesValue:
        """Convert to lowercase."""
        from ...morphisms.bytes_ import BytesLowerOp

        return cast("BytesValue", self._wrap_bytes_result(BytesLowerOp(self)))

    def strip(self, chars: BytesArg | None = None) -> BytesValue:
        """Strip whitespace or chars."""
        from ...morphisms.bytes_ import BytesStripOp

        return cast("BytesValue", self._wrap_bytes_result(BytesStripOp(self, chars)))

    def lstrip(self, chars: BytesArg | None = None) -> BytesValue:
        """Strip leading whitespace or chars."""
        from ...morphisms.bytes_ import BytesLStripOp

        return cast("BytesValue", self._wrap_bytes_result(BytesLStripOp(self, chars)))

    def rstrip(self, chars: BytesArg | None = None) -> BytesValue:
        """Strip trailing whitespace or chars."""
        from ...morphisms.bytes_ import BytesRStripOp

        return cast("BytesValue", self._wrap_bytes_result(BytesRStripOp(self, chars)))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListValue[bytes]:
        """Split bytes."""
        from ...morphisms.bytes_ import BytesSplitOp
        from ...values import ListValue

        if sep is not None:
            return ListValue(BytesSplitOp(self, sep, maxsplit))
        return ListValue(BytesSplitOp(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntValue:
        """Find sub-bytes."""
        from ...morphisms.bytes_ import BytesFindOp
        from ...values import IntValue

        return IntValue(BytesFindOp(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> IntValue:
        """Count sub-bytes occurrences."""
        from ...morphisms.bytes_ import BytesCountOp
        from ...values import IntValue

        return IntValue(BytesCountOp(self, sub))

    def startswith(self, prefix: BytesArg) -> BoolValue:
        """Check if starts with prefix."""
        from ...morphisms.bytes_ import BytesStartsWithOp
        from ...values import BoolValue

        return BoolValue(BytesStartsWithOp(self, prefix))

    def endswith(self, suffix: BytesArg) -> BoolValue:
        """Check if ends with suffix."""
        from ...morphisms.bytes_ import BytesEndsWithOp
        from ...values import BoolValue

        return BoolValue(BytesEndsWithOp(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> BytesValue:
        """Replace sub-bytes."""
        from ...morphisms.bytes_ import BytesReplaceOp

        return cast("BytesValue", self._wrap_bytes_result(BytesReplaceOp(self, old, new, count)))
