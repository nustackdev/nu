"""Integer type for Term expressions.

This module provides IntType which represents integer expressions (literal or computed).
Supports arithmetic, comparison, logical, and bitwise operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from .bases import BaseType, BitwiseBase, ComparisonBase, LogicalBase


if TYPE_CHECKING:
    from every._abc import Term

    from .bool import BoolType  # noqa: F401
    from .float import FloatType


__all__ = [
    "IntType",
]


class IntType(
    ComparisonBase["int | float | FloatType | IntType"],
    LogicalBase["bool | int | BoolType | IntType", "BoolType"],
    BitwiseBase["int | IntType", "IntType"],
    BaseType[int],
):
    """Integer type - represents int expressions (literal or computed).

    Supports arithmetic, comparison, logical, and bitwise operations.
    Operations return appropriate Type classes matching Python semantics:
    - int + int -> IntType
    - int + float -> FloatType
    - int / int -> FloatType (true division)

    Example:
        >>> x = IntType(42)  # From literal
        >>> y = IntType(some_op)  # From operation
        >>> z = x + y  # Returns IntType
        >>> z.execute(ctx)  # Returns computed int
    """

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        return IntType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)

    # =========================================================================
    # ARITHMETIC OPERATIONS
    # =========================================================================

    @overload
    def __add__(self, other: int | IntType) -> IntType: ...
    @overload
    def __add__(self, other: float | FloatType) -> FloatType: ...
    def __add__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from term.ops import AddOp

        from .float import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(AddOp(self, other))
        return IntType(AddOp(self, other))

    @overload
    def __radd__(self, other: int) -> IntType: ...
    @overload
    def __radd__(self, other: float) -> FloatType: ...
    def __radd__(self, other: int | float) -> IntType | FloatType:
        from term.ops import AddOp

        from .float import FloatType

        if isinstance(other, float):
            return FloatType(AddOp(other, self))
        return IntType(AddOp(other, self))

    @overload
    def __sub__(self, other: int | IntType) -> IntType: ...
    @overload
    def __sub__(self, other: float | FloatType) -> FloatType: ...
    def __sub__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from term.ops import SubOp

        from .float import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(SubOp(self, other))
        return IntType(SubOp(self, other))

    @overload
    def __rsub__(self, other: int) -> IntType: ...
    @overload
    def __rsub__(self, other: float) -> FloatType: ...
    def __rsub__(self, other: int | float) -> IntType | FloatType:
        from term.ops import SubOp

        from .float import FloatType

        if isinstance(other, float):
            return FloatType(SubOp(other, self))
        return IntType(SubOp(other, self))

    @overload
    def __mul__(self, other: int | IntType) -> IntType: ...
    @overload
    def __mul__(self, other: float | FloatType) -> FloatType: ...
    def __mul__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from term.ops import MulOp

        from .float import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(MulOp(self, other))
        return IntType(MulOp(self, other))

    @overload
    def __rmul__(self, other: int) -> IntType: ...
    @overload
    def __rmul__(self, other: float) -> FloatType: ...
    def __rmul__(self, other: int | float) -> IntType | FloatType:
        from term.ops import MulOp

        from .float import FloatType

        if isinstance(other, float):
            return FloatType(MulOp(other, self))
        return IntType(MulOp(other, self))

    def __truediv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from term.ops import DivOp

        from .float import FloatType

        return FloatType(DivOp(self, other))

    def __rtruediv__(self, other: int | float) -> FloatType:
        from term.ops import DivOp

        from .float import FloatType

        return FloatType(DivOp(other, self))

    @overload
    def __floordiv__(self, other: int | IntType) -> IntType: ...
    @overload
    def __floordiv__(self, other: float | FloatType) -> FloatType: ...
    def __floordiv__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from term.ops import FloorDivOp

        from .float import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(FloorDivOp(self, other))
        return IntType(FloorDivOp(self, other))

    @overload
    def __rfloordiv__(self, other: int) -> IntType: ...
    @overload
    def __rfloordiv__(self, other: float) -> FloatType: ...
    def __rfloordiv__(self, other: int | float) -> IntType | FloatType:
        from term.ops import FloorDivOp

        from .float import FloatType

        if isinstance(other, float):
            return FloatType(FloorDivOp(other, self))
        return IntType(FloorDivOp(other, self))

    @overload
    def __mod__(self, other: int | IntType) -> IntType: ...
    @overload
    def __mod__(self, other: float | FloatType) -> FloatType: ...
    def __mod__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from term.ops import ModOp

        from .float import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(ModOp(self, other))
        return IntType(ModOp(self, other))

    @overload
    def __rmod__(self, other: int) -> IntType: ...
    @overload
    def __rmod__(self, other: float) -> FloatType: ...
    def __rmod__(self, other: int | float) -> IntType | FloatType:
        from term.ops import ModOp

        from .float import FloatType

        if isinstance(other, float):
            return FloatType(ModOp(other, self))
        return IntType(ModOp(other, self))

    @overload
    def __pow__(self, other: int | IntType) -> IntType: ...
    @overload
    def __pow__(self, other: float | FloatType) -> FloatType: ...
    def __pow__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from term.ops import PowOp

        from .float import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(PowOp(self, other))
        return IntType(PowOp(self, other))

    @overload
    def __rpow__(self, other: int) -> IntType: ...
    @overload
    def __rpow__(self, other: float) -> FloatType: ...
    def __rpow__(self, other: int | float) -> IntType | FloatType:
        from term.ops import PowOp

        from .float import FloatType

        if isinstance(other, float):
            return FloatType(PowOp(other, self))
        return IntType(PowOp(other, self))

    def __neg__(self) -> IntType:
        from term.ops import NegOp

        return IntType(NegOp(self))

    def __pos__(self) -> IntType:
        from term.ops import PosOp

        return IntType(PosOp(self))

    def __abs__(self) -> IntType:
        from term.ops import AbsOp

        return IntType(AbsOp(self))
