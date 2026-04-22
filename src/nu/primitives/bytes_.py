"""BytesI - bytes interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from nu.terms import BytesArg, IntArg, StrArg

    from .bool_ import BoolI
    from .int_ import IntI
    from .str_ import StrI


__all__ = [
    "BytesI",
]


class BytesI(Interface, TypedNu[bytes]):
    """Bytes interface. Sliceable + comparable + logical + bytes methods."""

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: BytesArg) -> BytesI:
        from nu.interactions import Add

        return BytesI(Add(self, other))

    def __radd__(self, other: BytesArg) -> BytesI:
        from nu.interactions import Add

        return BytesI(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> IntI: ...
    @overload
    def __getitem__(self, key: slice) -> BytesI: ...
    def __getitem__(self, key: IntArg | slice) -> BytesI | IntI:
        from nu.interactions import At, Slice

        from .int_ import IntI

        if isinstance(key, slice):
            return BytesI(Slice(self, key.start, key.stop, key.step))
        return IntI(At(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BytesArg) -> BoolI:
        from nu.interactions import Gt

        from .bool_ import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: BytesArg) -> BoolI:
        from nu.interactions import Lt

        from .bool_ import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: BytesArg) -> BoolI:
        from nu.interactions import Ge

        from .bool_ import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: BytesArg) -> BoolI:
        from nu.interactions import Le

        from .bool_ import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: BytesArg) -> BoolI:
        from nu.interactions import Eq

        from .bool_ import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: BytesArg) -> BoolI:
        from nu.interactions import Ne

        from .bool_ import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: BytesArg) -> BoolI:
        from nu.interactions import IdComp

        from .bool_ import BoolI

        return BoolI(IdComp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BytesArg) -> BoolI:
        from nu.interactions import And

        from .bool_ import BoolI

        return BoolI(And(self, other))

    def or_(self, other: BytesArg) -> BoolI:
        from nu.interactions import Or

        from .bool_ import BoolI

        return BoolI(Or(self, other))

    def not_(self) -> BoolI:
        from nu.interactions import Not

        from .bool_ import BoolI

        return BoolI(Not(self))

    def bool_(self) -> BoolI:
        from nu.interactions import Bool

        from .bool_ import BoolI

        return BoolI(Bool(self))

    # =========================================================================
    # BYTES METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> StrI:
        from .bytes_ops import DecodeOp
        from .str_ import StrI

        return StrI(DecodeOp(self, encoding))

    def hex_(self) -> StrI:
        from .bytes_ops import HexOp
        from .str_ import StrI

        return StrI(HexOp(self))

    def upper(self) -> BytesI:
        from .bytes_ops import BytesUpperOp

        return BytesI(BytesUpperOp(self))

    def lower(self) -> BytesI:
        from .bytes_ops import BytesLowerOp

        return BytesI(BytesLowerOp(self))

    def strip(self, chars: BytesArg | None = None) -> BytesI:
        from .bytes_ops import BytesStripOp

        return BytesI(BytesStripOp(self, chars))

    def lstrip(self, chars: BytesArg | None = None) -> BytesI:
        from .bytes_ops import BytesLStripOp

        return BytesI(BytesLStripOp(self, chars))

    def rstrip(self, chars: BytesArg | None = None) -> BytesI:
        from .bytes_ops import BytesRStripOp

        return BytesI(BytesRStripOp(self, chars))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListI:
        from ..collections.list_ import ListI
        from .bytes_ops import BytesSplitOp

        if sep is not None:
            return ListI(BytesSplitOp(self, sep, maxsplit))
        return ListI(BytesSplitOp(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntI:
        from .bytes_ops import BytesFindOp
        from .int_ import IntI

        return IntI(BytesFindOp(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> IntI:
        from .bytes_ops import BytesCountOp
        from .int_ import IntI

        return IntI(BytesCountOp(self, sub))

    def startswith(self, prefix: BytesArg) -> BoolI:
        from .bool_ import BoolI
        from .bytes_ops import BytesStartsWithOp

        return BoolI(BytesStartsWithOp(self, prefix))

    def endswith(self, suffix: BytesArg) -> BoolI:
        from .bool_ import BoolI
        from .bytes_ops import BytesEndsWithOp

        return BoolI(BytesEndsWithOp(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> BytesI:
        from .bytes_ops import BytesReplaceOp

        return BytesI(BytesReplaceOp(self, old, new, count))
