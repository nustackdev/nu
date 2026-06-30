"""BytesForm - bytes interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import Form, TypedNu


if TYPE_CHECKING:
    from nu.terms import BytesArg, IntArg, StrArg

    from .bool_ import BoolForm
    from .int_ import IntForm
    from .str_ import StrForm


__all__ = [
    "BytesForm",
]


class BytesForm(Form, TypedNu[bytes]):
    """Bytes interface. Sliceable + comparable + logical + bytes methods."""

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: BytesArg) -> BytesForm:
        from nu import Add

        return BytesForm(Add(self, other))

    def __radd__(self, other: BytesArg) -> BytesForm:
        from nu import Add

        return BytesForm(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> IntForm: ...
    @overload
    def __getitem__(self, key: slice) -> BytesForm: ...
    def __getitem__(self, key: IntArg | slice) -> BytesForm | IntForm:
        from nu import At, Slice

        from .int_ import IntForm

        if isinstance(key, slice):
            return BytesForm(Slice(self, key.start, key.stop, key.step))
        return IntForm(At(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BytesArg) -> BoolForm:
        from nu import Gt

        from .bool_ import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: BytesArg) -> BoolForm:
        from nu import Lt

        from .bool_ import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: BytesArg) -> BoolForm:
        from nu import Ge

        from .bool_ import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: BytesArg) -> BoolForm:
        from nu import Le

        from .bool_ import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: BytesArg) -> BoolForm:  # type: ignore[override]
        from nu import Eq

        from .bool_ import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: BytesArg) -> BoolForm:  # type: ignore[override]
        from nu import Ne

        from .bool_ import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: BytesArg) -> BoolForm:
        from nu import IdComp

        from .bool_ import BoolForm

        return BoolForm(IdComp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BytesArg) -> BoolForm:
        from nu import And

        from .bool_ import BoolForm

        return BoolForm(And(self, other))

    def or_(self, other: BytesArg) -> BoolForm:
        from nu import Or

        from .bool_ import BoolForm

        return BoolForm(Or(self, other))

    def not_(self) -> BoolForm:
        from nu import Not

        from .bool_ import BoolForm

        return BoolForm(Not(self))

    def bool_(self) -> BoolForm:
        from nu import Bool

        from .bool_ import BoolForm

        return BoolForm(Bool(self))

    # =========================================================================
    # BYTES METHODS
    # =========================================================================

    def decode(self, encoding: StrArg = "utf-8") -> StrForm:
        from .bytes_ops import DecodeOp
        from .str_ import StrForm

        return StrForm(DecodeOp(self, encoding))

    def hex_(self) -> StrForm:
        from .bytes_ops import HexOp
        from .str_ import StrForm

        return StrForm(HexOp(self))

    def upper(self) -> BytesForm:
        from .bytes_ops import BytesUpperOp

        return BytesForm(BytesUpperOp(self))

    def lower(self) -> BytesForm:
        from .bytes_ops import BytesLowerOp

        return BytesForm(BytesLowerOp(self))

    def strip(self, chars: BytesArg | None = None) -> BytesForm:
        from .bytes_ops import BytesStripOp

        return BytesForm(BytesStripOp(self, chars))

    def lstrip(self, chars: BytesArg | None = None) -> BytesForm:
        from .bytes_ops import BytesLStripOp

        return BytesForm(BytesLStripOp(self, chars))

    def rstrip(self, chars: BytesArg | None = None) -> BytesForm:
        from .bytes_ops import BytesRStripOp

        return BytesForm(BytesRStripOp(self, chars))

    def split_bytes(self, sep: BytesArg | None = None, maxsplit: IntArg = -1) -> ListForm:
        from ..forms.collections.list_ import ListForm
        from .bytes_ops import BytesSplitOp

        if sep is not None:
            return ListForm(BytesSplitOp(self, sep, maxsplit))
        return ListForm(BytesSplitOp(self, None, maxsplit))

    def find_bytes(self, sub: BytesArg, start: IntArg = 0, end: IntArg | None = None) -> IntForm:
        from .bytes_ops import BytesFindOp
        from .int_ import IntForm

        return IntForm(BytesFindOp(self, sub, start, end))

    def count_bytes(self, sub: BytesArg) -> IntForm:
        from .bytes_ops import BytesCountOp
        from .int_ import IntForm

        return IntForm(BytesCountOp(self, sub))

    def startswith(self, prefix: BytesArg) -> BoolForm:
        from .bool_ import BoolForm
        from .bytes_ops import BytesStartsWithOp

        return BoolForm(BytesStartsWithOp(self, prefix))

    def endswith(self, suffix: BytesArg) -> BoolForm:
        from .bool_ import BoolForm
        from .bytes_ops import BytesEndsWithOp

        return BoolForm(BytesEndsWithOp(self, suffix))

    def replace(self, old: BytesArg, new: BytesArg, count: IntArg = -1) -> BytesForm:
        from .bytes_ops import BytesReplaceOp

        return BytesForm(BytesReplaceOp(self, old, new, count))
