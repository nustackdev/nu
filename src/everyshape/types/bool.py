"""Boolean type for Term expressions.

This module provides BoolType which represents boolean expressions (literal or computed).
Supports logical operations: and_(), or_(), not_().
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import ComparisonBase, LogicalBase, Type


if TYPE_CHECKING:
    from everyshape.term import Term


__all__ = [
    "BoolType",
]


class BoolType(
    LogicalBase["bool | BoolType", "BoolType"],
    ComparisonBase["bool | BoolType"],
    Type[bool],
):
    """Boolean type - represents bool expressions (literal or computed).

    Supports logical operations: and_(), or_(), not_().

    Example:
        >>> x = BoolType(True)
        >>> y = x.and_(other)  # Returns BoolType
        >>> z = x.not_()  # Returns BoolType
    """

    def _wrap_logical_result(self, operand: Term) -> Term:
        return BoolType(operand)

    def _wrap_comparison_result(self, operand: Term) -> Term:
        return BoolType(operand)
