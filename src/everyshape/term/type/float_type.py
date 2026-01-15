"""Float type for Term expressions.

This module provides FloatType which represents float expressions (literal or computed).
Supports arithmetic, comparison, and logical operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base_comparison import ComparisonBase
from .base_logical import LogicalBase
from .type import Type


if TYPE_CHECKING:
    from ..term import Term
    from .bool_type import BoolType  # noqa: F401
    from .int_type import IntType


__all__ = [
    "FloatType",
]


class FloatType(
    ComparisonBase["int | float | FloatType | IntType"],
    LogicalBase["bool | float | BoolType | FloatType", "BoolType"],
    Type[float],
):
    """Float type - represents float expressions (literal or computed).

    Supports arithmetic, comparison, and logical operations.
    All arithmetic operations return FloatType (Python semantics).

    Example:
        >>> x = FloatType(3.14)  # From literal
        >>> y = FloatType(some_op)  # From operation
        >>> z = x * 2  # Returns FloatType
    """

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from .bool_type import BoolType

        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool_type import BoolType

        return BoolType(operand)

    # All arithmetic returns FloatType
    def __add__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comp.binary_ops import AddOp
        from ..conversion import literal

        return FloatType(AddOp(self, literal(other)))

    def __radd__(self, other: int | float) -> FloatType:
        from ..comp.binary_ops import AddOp
        from ..conversion import literal

        return FloatType(AddOp(literal(other), self))

    def __sub__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comp.binary_ops import SubOp
        from ..conversion import literal

        return FloatType(SubOp(self, literal(other)))

    def __rsub__(self, other: int | float) -> FloatType:
        from ..comp.binary_ops import SubOp
        from ..conversion import literal

        return FloatType(SubOp(literal(other), self))

    def __mul__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comp.binary_ops import MulOp
        from ..conversion import literal

        return FloatType(MulOp(self, literal(other)))

    def __rmul__(self, other: int | float) -> FloatType:
        from ..comp.binary_ops import MulOp
        from ..conversion import literal

        return FloatType(MulOp(literal(other), self))

    def __truediv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comp.binary_ops import DivOp
        from ..conversion import literal

        return FloatType(DivOp(self, literal(other)))

    def __rtruediv__(self, other: int | float) -> FloatType:
        from ..comp.binary_ops import DivOp
        from ..conversion import literal

        return FloatType(DivOp(literal(other), self))

    def __floordiv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comp.binary_ops import FloorDivOp
        from ..conversion import literal

        return FloatType(FloorDivOp(self, literal(other)))

    def __rfloordiv__(self, other: int | float) -> FloatType:
        from ..comp.binary_ops import FloorDivOp
        from ..conversion import literal

        return FloatType(FloorDivOp(literal(other), self))

    def __mod__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comp.binary_ops import ModOp
        from ..conversion import literal

        return FloatType(ModOp(self, literal(other)))

    def __rmod__(self, other: int | float) -> FloatType:
        from ..comp.binary_ops import ModOp
        from ..conversion import literal

        return FloatType(ModOp(literal(other), self))

    def __pow__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comp.binary_ops import PowOp
        from ..conversion import literal

        return FloatType(PowOp(self, literal(other)))

    def __rpow__(self, other: int | float) -> FloatType:
        from ..comp.binary_ops import PowOp
        from ..conversion import literal

        return FloatType(PowOp(literal(other), self))

    def __neg__(self) -> FloatType:
        from ..comp.unary_ops import NegOp

        return FloatType(NegOp(self))

    def __pos__(self) -> FloatType:
        from ..comp.unary_ops import PosOp

        return FloatType(PosOp(self))

    def __abs__(self) -> FloatType:
        from ..comp.unary_ops import AbsOp

        return FloatType(AbsOp(self))
