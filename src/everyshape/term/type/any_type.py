"""Any type for Term expressions.

This module provides AnyType which represents expressions of unknown/dynamic type.
AnyType can be any type and supports all operations. Results remain as AnyType
until resolved.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base_arithmetic import NumericBase
from .base_bitwise import BitwiseBase
from .base_comparison import ComparisonBase
from .base_logical import LogicalBase
from .type import Type


if TYPE_CHECKING:
    from ..term import Term


__all__ = [
    "AnyType",
]


class AnyType(
    NumericBase["object", "AnyType"],
    ComparisonBase["object"],
    LogicalBase["object", "BoolType"],
    BitwiseBase["object", "AnyType"],
    Type[object],
):
    """Any type - represents expressions of unknown/dynamic type.

    AnyType can be any type and supports all operations.
    Results remain as AnyType until resolved.

    Useful for:
    - Dynamic lookups where type is not known at definition time
    - Generic operations that work on any value

    Example:
        >>> x = AnyType(some_dynamic_data)
        >>> y = x + 1  # Returns AnyType
        >>> z = x.is_empty()  # Returns BoolType
    """

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        return AnyType(operand)

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        return AnyType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        from .bool_type import BoolType

        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool_type import BoolType

        return BoolType(operand)
