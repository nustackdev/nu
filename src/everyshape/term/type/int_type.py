"""Integer type for Term expressions.

This module provides IntType which represents integer expressions (literal or computed).
Supports arithmetic, comparison, logical, and bitwise operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from .base_bitwise import BitwiseBase
from .base_comparison import ComparisonBase
from .base_logical import LogicalBase
from .type import Type


if TYPE_CHECKING:
    from ..term import Term
    from .bool_type import BoolType  # noqa: F401
    from .float_type import FloatType


__all__ = [
    "IntType",
]


class IntType(
    ComparisonBase["int | float | FloatType | IntType"],
    LogicalBase["bool | int | BoolType | IntType", "BoolType"],
    BitwiseBase["int | IntType", "IntType"],
    Type[int],
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
        from .bool_type import BoolType

        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool_type import BoolType

        return BoolType(operand)

    # =========================================================================
    # ARITHMETIC OPERATIONS
    # =========================================================================

    @overload
    def __add__(self, other: int | IntType) -> IntType: ...
    @overload
    def __add__(self, other: float | FloatType) -> FloatType: ...
    def __add__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import AddOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(AddOp(self, literal(other)))
        return IntType(AddOp(self, literal(other)))

    @overload
    def __radd__(self, other: int) -> IntType: ...
    @overload
    def __radd__(self, other: float) -> FloatType: ...
    def __radd__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import AddOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, float):
            return FloatType(AddOp(literal(other), self))
        return IntType(AddOp(literal(other), self))

    @overload
    def __sub__(self, other: int | IntType) -> IntType: ...
    @overload
    def __sub__(self, other: float | FloatType) -> FloatType: ...
    def __sub__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import SubOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(SubOp(self, literal(other)))
        return IntType(SubOp(self, literal(other)))

    @overload
    def __rsub__(self, other: int) -> IntType: ...
    @overload
    def __rsub__(self, other: float) -> FloatType: ...
    def __rsub__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import SubOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, float):
            return FloatType(SubOp(literal(other), self))
        return IntType(SubOp(literal(other), self))

    @overload
    def __mul__(self, other: int | IntType) -> IntType: ...
    @overload
    def __mul__(self, other: float | FloatType) -> FloatType: ...
    def __mul__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import MulOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(MulOp(self, literal(other)))
        return IntType(MulOp(self, literal(other)))

    @overload
    def __rmul__(self, other: int) -> IntType: ...
    @overload
    def __rmul__(self, other: float) -> FloatType: ...
    def __rmul__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import MulOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, float):
            return FloatType(MulOp(literal(other), self))
        return IntType(MulOp(literal(other), self))

    def __truediv__(self, other: int | float | IntType | FloatType) -> FloatType:
        from ..comps.core.binary_ops import DivOp
        from ..conversion import literal
        from .float_type import FloatType

        return FloatType(DivOp(self, literal(other)))

    def __rtruediv__(self, other: int | float) -> FloatType:
        from ..comps.core.binary_ops import DivOp
        from ..conversion import literal
        from .float_type import FloatType

        return FloatType(DivOp(literal(other), self))

    @overload
    def __floordiv__(self, other: int | IntType) -> IntType: ...
    @overload
    def __floordiv__(self, other: float | FloatType) -> FloatType: ...
    def __floordiv__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import FloorDivOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(FloorDivOp(self, literal(other)))
        return IntType(FloorDivOp(self, literal(other)))

    @overload
    def __rfloordiv__(self, other: int) -> IntType: ...
    @overload
    def __rfloordiv__(self, other: float) -> FloatType: ...
    def __rfloordiv__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import FloorDivOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, float):
            return FloatType(FloorDivOp(literal(other), self))
        return IntType(FloorDivOp(literal(other), self))

    @overload
    def __mod__(self, other: int | IntType) -> IntType: ...
    @overload
    def __mod__(self, other: float | FloatType) -> FloatType: ...
    def __mod__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import ModOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(ModOp(self, literal(other)))
        return IntType(ModOp(self, literal(other)))

    @overload
    def __rmod__(self, other: int) -> IntType: ...
    @overload
    def __rmod__(self, other: float) -> FloatType: ...
    def __rmod__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import ModOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, float):
            return FloatType(ModOp(literal(other), self))
        return IntType(ModOp(literal(other), self))

    @overload
    def __pow__(self, other: int | IntType) -> IntType: ...
    @overload
    def __pow__(self, other: float | FloatType) -> FloatType: ...
    def __pow__(self, other: int | float | IntType | FloatType) -> IntType | FloatType:
        from ..comps.core.binary_ops import PowOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, (float, FloatType)):
            return FloatType(PowOp(self, literal(other)))
        return IntType(PowOp(self, literal(other)))

    @overload
    def __rpow__(self, other: int) -> IntType: ...
    @overload
    def __rpow__(self, other: float) -> FloatType: ...
    def __rpow__(self, other: int | float) -> IntType | FloatType:
        from ..comps.core.binary_ops import PowOp
        from ..conversion import literal
        from .float_type import FloatType

        if isinstance(other, float):
            return FloatType(PowOp(literal(other), self))
        return IntType(PowOp(literal(other), self))

    def __neg__(self) -> IntType:
        from ..comps.core.unary_ops import NegOp

        return IntType(NegOp(self))

    def __pos__(self) -> IntType:
        from ..comps.core.unary_ops import PosOp

        return IntType(PosOp(self))

    def __abs__(self) -> IntType:
        from ..comps.core.unary_ops import AbsOp

        return IntType(AbsOp(self))
