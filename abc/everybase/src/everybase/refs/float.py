"""Float ref base combining numeric traits.

FloatRefBase = RefBase[float] + Numeric + Comparable + Logical
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.capabilities import ComparableBase, LogicalBase, NumericBase

from .base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef, FloatRef, IntRef  # noqa: F401


__all__ = [
    "FloatRefBase",
]


class FloatRefBase(
    NumericBase["int | float | IntRef | FloatRef", "FloatRef"],
    ComparableBase["int | float | IntRef | FloatRef"],
    LogicalBase["bool | float | BoolRef | FloatRef", "BoolRef"],
    RefBase[float],
):
    """Abstract base for float refs.

    Combines:
    - Numeric: +, -, *, /, //, %, **, neg, pos, abs
    - Comparable: >, <, >=, <=, eq(), ne(), is_()
    - Logical: and_(), or_(), not_(), bool_()

    Concrete implementations must add get() for their storage substrate.
    """

    def _wrap_arithmetic_result(self, operand: Term) -> FloatRef:
        from everybase.py.float import FloatRef

        return FloatRef(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def __neg__(self) -> FloatRef:
        from everybase.morphisms import NegOp
        from everybase.py.float import FloatRef

        return FloatRef(NegOp(self))

    def __pos__(self) -> FloatRef:
        from everybase.morphisms import PosOp
        from everybase.py.float import FloatRef

        return FloatRef(PosOp(self))

    def __abs__(self) -> FloatRef:
        from everybase.morphisms import AbsOp
        from everybase.py.float import FloatRef

        return FloatRef(AbsOp(self))
