"""Boolean ref base combining logical traits.

BoolType = TypeBase[bool] + Logical + Comparable
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...capabilities import ComparableBase, LogicalBase
from ..base import TypeBase


if TYPE_CHECKING:
    from everybase.core import BoolArg, Term  # noqa: F401

    from ...values import BoolValue


__all__ = [
    "BoolType",
]


class BoolType(
    LogicalBase["BoolArg", "BoolValue"],
    ComparableBase["BoolArg"],
    TypeBase[bool],
):
    """Abstract base for boolean refs.

    Combines:
    - Logical: and_(), or_(), not_(), bool_()
    - Comparable: >, <, >=, <=, eq(), ne(), is_()

    Concrete implementations must add get() for their storage substrate.
    """

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)
