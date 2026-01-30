"""Bytes ref base combining sequence traits.

BytesRefBase = RefBase[bytes] + Lengthable + Sliceable + Containable + Comparable + Logical

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

from ._base import RefBase


if TYPE_CHECKING:
    from everyabc import BytesArg, IntArg, StrArg, Term
    from everybase.py import BoolRef, BytesRef, IntRef, ListRef, StrRef


__all__ = [
    "BytesRefBase",
]


class BytesRefBase(
    LengthableBase,
    SliceableBase["BytesRef"],
    ContainableBase["int | bytes"],
    ComparableBase["bytes | BytesRef"],
    LogicalBase["bytes | BytesRef", "BoolRef"],
    RefBase[bytes],
):
    """Abstract base for bytes refs.

    Combines sequence and comparison traits, returns concrete py types.
    """

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py import BoolRef

        return BoolRef(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py import BoolRef

        return BoolRef(operand)

    def _wrap_bytes_result(self, operand: Term) -> BytesRef:
        from everybase.py import BytesRef

        return BytesRef(operand)

    def _wrap_sliceable_result(self, operand: Term) -> BytesRef:
        from everybase.py import BytesRef

        return BytesRef(operand)

    def __add__(self, other: bytes | BytesRefBase) -> BytesRef:
        from everybase.morphisms import AddOp
        from everybase.py import BytesRef

        return BytesRef(AddOp(self, other))

    def __radd__(self, other: bytes) -> BytesRef:
        from everybase.morphisms import AddOp
        from everybase.py import BytesRef

        return BytesRef(AddOp(other, self))

    @overload
    def __getitem__(self, key: int) -> IntRef: ...
    @overload
    def __getitem__(self, key: slice) -> BytesRef: ...
    def __getitem__(self, key: int | slice) -> BytesRef | IntRef:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.py import BytesRef, IntRef

        if isinstance(key, slice):
            return BytesRef(SliceOp(self, key.start, key.stop, key.step))
        return IntRef(AtOp(self, key))

    # =========================================================================
    # BYTES-SPECIFIC METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> StrRef:
        """Decode bytes to string."""
        from everybase.morphisms.type_bytes import DecodeOp
        from everybase.py import StrRef

        return StrRef(DecodeOp(self, encoding))

    def hex_(self) -> StrRef:
        """Convert to hex string."""
        from everybase.morphisms.type_bytes import HexOp
        from everybase.py import StrRef

        return StrRef(HexOp(self))

    def upper(self) -> BytesRef:
        """Convert to uppercase."""
        from everybase.morphisms.type_bytes import BytesUpperOp

        return cast("BytesRef", self._wrap_bytes_result(BytesUpperOp(self)))

    def lower(self) -> BytesRef:
        """Convert to lowercase."""
        from everybase.morphisms.type_bytes import BytesLowerOp

        return cast("BytesRef", self._wrap_bytes_result(BytesLowerOp(self)))

    def strip(self, chars: BytesArg | None = None) -> BytesRef:
        """Strip whitespace or chars."""
        from everybase.morphisms.type_bytes import BytesStripOp

        if chars is not None:
            return cast("BytesRef", self._wrap_bytes_result(BytesStripOp(self, chars)))
        return cast("BytesRef", self._wrap_bytes_result(BytesStripOp(self)))

    def lstrip(self, chars: BytesArg | None = None) -> BytesRef:
        """Strip leading whitespace or chars."""
        from everybase.morphisms.type_bytes import BytesLStripOp

        if chars is not None:
            return cast("BytesRef", self._wrap_bytes_result(BytesLStripOp(self, chars)))
        return cast("BytesRef", self._wrap_bytes_result(BytesLStripOp(self)))

    def rstrip(self, chars: BytesArg | None = None) -> BytesRef:
        """Strip trailing whitespace or chars."""
        from everybase.morphisms.type_bytes import BytesRStripOp

        if chars is not None:
            return cast("BytesRef", self._wrap_bytes_result(BytesRStripOp(self, chars)))
        return cast("BytesRef", self._wrap_bytes_result(BytesRStripOp(self)))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListRef[bytes]:
        """Split bytes."""
        from everybase.morphisms.type_bytes import BytesSplitOp
        from everybase.py import ListRef

        if sep is not None:
            return ListRef(BytesSplitOp(self, sep, maxsplit))
        return ListRef(BytesSplitOp(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntRef:
        """Find sub-bytes."""
        from everybase.morphisms.type_bytes import BytesFindOp
        from everybase.py import IntRef

        return IntRef(BytesFindOp(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> IntRef:
        """Count sub-bytes occurrences."""
        from everybase.morphisms.type_bytes import BytesCountOp
        from everybase.py import IntRef

        return IntRef(BytesCountOp(self, sub))

    def startswith(self, prefix: BytesArg) -> BoolRef:
        """Check if starts with prefix."""
        from everybase.morphisms.type_bytes import BytesStartsWithOp
        from everybase.py import BoolRef

        return BoolRef(BytesStartsWithOp(self, prefix))

    def endswith(self, suffix: BytesArg) -> BoolRef:
        """Check if ends with suffix."""
        from everybase.morphisms.type_bytes import BytesEndsWithOp
        from everybase.py import BoolRef

        return BoolRef(BytesEndsWithOp(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> BytesRef:
        """Replace sub-bytes."""
        from everybase.morphisms.type_bytes import BytesReplaceOp

        return cast("BytesRef", self._wrap_bytes_result(BytesReplaceOp(self, old, new, count)))
