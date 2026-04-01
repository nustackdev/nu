"""None ref base for nil/null values.

NoneType = Object[None] + Logical

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...capabilities import LogicalBase
from ..object import Object


if TYPE_CHECKING:
    from nu.terms import NoneArg, Term  # noqa: F401

    from ...values import BoolValue, NoneValue  # noqa: F401


__all__ = [
    "NoneType",
]


class NoneType(
    LogicalBase["NoneArg", "BoolValue"],
    Object[None],
):
    """Abstract base for None/nil refs.

    Represents absence of a value (distinct from Empty sentinel).
    """

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)
