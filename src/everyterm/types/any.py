"""Any type for Term expressions.

This module provides AnyType which represents expressions of unknown/dynamic type.
AnyType can be any type and supports all operations. Results remain as AnyType
until resolved.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import (
    BaseType,
    BitwiseBase,
    ComparisonBase,
    LogicalBase,
    NumericBase,
)


if TYPE_CHECKING:
    from everyterm.term import Term

    from .bool import BoolType  # noqa: F401


__all__ = [
    "AnyType",
]


class AnyType(
    NumericBase["object", "AnyType"],
    ComparisonBase["object"],
    LogicalBase["object", "BoolType"],
    BitwiseBase["object", "AnyType"],
    BaseType[object],
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
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_logical_result(self, operand: Term) -> Term:
        from .bool import BoolType

        return BoolType(operand)
