"""Boolean ref base combining logical traits.

BoolType = TypeBase[bool] + Logical + Comparable
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.capabilities import ComparableBase, LogicalBase

from .base import TypeBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.values import BoolValue


__all__ = [
    "BoolType",
]


class BoolType(
    LogicalBase["bool | BoolValue", "BoolValue"],
    ComparableBase["bool | BoolValue"],
    TypeBase[bool],
):
    """Abstract base for boolean refs.

    Combines:
    - Logical: and_(), or_(), not_(), bool_()
    - Comparable: >, <, >=, <=, eq(), ne(), is_()

    Concrete implementations must add get() for their storage substrate.
    """

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)
