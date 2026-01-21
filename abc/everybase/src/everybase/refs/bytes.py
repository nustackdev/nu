"""Bytes ref base combining sequence traits.

BytesRefBase = RefBase[bytes] + Lengthable + Sliceable + Containable + Comparable + Logical

Returns concrete py types.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, cast, overload

from everybase.traits import Comparable, Containable, Lengthable, Logical, Sliceable

from .base import RefBase


if TYPE_CHECKING:
    from every import BytesArg, IntArg, StrArg, Term
    from everybase.py import BoolRef, BytesRef, IntRef, ListRef, StrRef


__all__ = [
    "BytesRefBase",
]


class BytesRefBase(
    Lengthable,
    Sliceable["BytesRef"],
    Containable["int | bytes"],
    Comparable["bytes | BytesRef"],
    Logical["bytes | BytesRef", "BoolRef"],
    RefBase[bytes],
    ABC,
):
    """Abstract base for bytes refs.

    Combines sequence and comparison traits, returns concrete py types.
    """

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_bytes_result(self, operand: Term) -> BytesRef:
        from everybase.py.bytes import BytesRef

        return BytesRef(operand)

    def _wrap_sliceable_result(self, operand: Term) -> BytesRef:
        from everybase.py.bytes import BytesRef

        return BytesRef(operand)

    def __add__(self, other: bytes | BytesRefBase) -> BytesRef:
        from everybase.morphisms import AddOp
        from everybase.py.bytes import BytesRef

        return BytesRef(AddOp(self, other))

    def __radd__(self, other: bytes) -> BytesRef:
        from everybase.morphisms import AddOp
        from everybase.py.bytes import BytesRef

        return BytesRef(AddOp(other, self))

    @overload
    def __getitem__(self, key: int) -> IntRef: ...
    @overload
    def __getitem__(self, key: slice) -> BytesRef: ...
    def __getitem__(self, key: int | slice) -> BytesRef | IntRef:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.py.bytes import BytesRef
        from everybase.py.int import IntRef

        if isinstance(key, slice):
            return BytesRef(SliceOp(self, key.start, key.stop, key.step))
        return IntRef(AtOp(self, key))

    # =========================================================================
    # BYTES-SPECIFIC METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> StrRef:
        """Decode bytes to string."""
        from everybase.morphisms.bytes_ops import DecodeOp
        from everybase.py.str import StrRef

        return StrRef(DecodeOp(self, encoding))

    def hex_(self) -> StrRef:
        """Convert to hex string."""
        from everybase.morphisms.bytes_ops import HexOp
        from everybase.py.str import StrRef

        return StrRef(HexOp(self))

    def upper(self) -> BytesRef:
        """Convert to uppercase."""
        from everybase.morphisms.bytes_ops import BytesUpperOp

        return cast("BytesRef", self._wrap_bytes_result(BytesUpperOp(self)))

    def lower(self) -> BytesRef:
        """Convert to lowercase."""
        from everybase.morphisms.bytes_ops import BytesLowerOp

        return cast("BytesRef", self._wrap_bytes_result(BytesLowerOp(self)))

    def strip(self, chars: BytesArg | None = None) -> BytesRef:
        """Strip whitespace or chars."""
        from everybase.morphisms.bytes_ops import BytesStripOp

        if chars is not None:
            return cast("BytesRef", self._wrap_bytes_result(BytesStripOp(self, chars)))
        return cast("BytesRef", self._wrap_bytes_result(BytesStripOp(self)))

    def lstrip(self, chars: BytesArg | None = None) -> BytesRef:
        """Strip leading whitespace or chars."""
        from everybase.morphisms.bytes_ops import BytesLStripOp

        if chars is not None:
            return cast("BytesRef", self._wrap_bytes_result(BytesLStripOp(self, chars)))
        return cast("BytesRef", self._wrap_bytes_result(BytesLStripOp(self)))

    def rstrip(self, chars: BytesArg | None = None) -> BytesRef:
        """Strip trailing whitespace or chars."""
        from everybase.morphisms.bytes_ops import BytesRStripOp

        if chars is not None:
            return cast("BytesRef", self._wrap_bytes_result(BytesRStripOp(self, chars)))
        return cast("BytesRef", self._wrap_bytes_result(BytesRStripOp(self)))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListRef[bytes]:
        """Split bytes."""
        from everybase.morphisms.bytes_ops import BytesSplitOp
        from everybase.py.list import ListRef

        if sep is not None:
            return ListRef(BytesSplitOp(self, sep, maxsplit))
        return ListRef(BytesSplitOp(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntRef:
        """Find sub-bytes."""
        from everybase.morphisms.bytes_ops import BytesFindOp
        from everybase.py.int import IntRef

        return IntRef(BytesFindOp(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> IntRef:
        """Count sub-bytes occurrences."""
        from everybase.morphisms.bytes_ops import BytesCountOp
        from everybase.py.int import IntRef

        return IntRef(BytesCountOp(self, sub))

    def startswith(self, prefix: BytesArg) -> BoolRef:
        """Check if starts with prefix."""
        from everybase.morphisms.bytes_ops import BytesStartsWithOp
        from everybase.py.bool import BoolRef

        return BoolRef(BytesStartsWithOp(self, prefix))

    def endswith(self, suffix: BytesArg) -> BoolRef:
        """Check if ends with suffix."""
        from everybase.morphisms.bytes_ops import BytesEndsWithOp
        from everybase.py.bool import BoolRef

        return BoolRef(BytesEndsWithOp(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> BytesRef:
        """Replace sub-bytes."""
        from everybase.morphisms.bytes_ops import BytesReplaceOp

        return cast("BytesRef", self._wrap_bytes_result(BytesReplaceOp(self, old, new, count)))
