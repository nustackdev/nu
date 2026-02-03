"""None ref base for nil/null values.

NoneType = TypeBase[None] + Logical

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..capabilities import LogicalBase
from .base import TypeBase


if TYPE_CHECKING:
    from everybase.core import Term

    from ..values import BoolValue, NoneValue  # noqa: F401


__all__ = [
    "NoneType",
]


class NoneType(
    LogicalBase["None | NoneValue", "BoolValue"],
    TypeBase[None],
):
    """Abstract base for None/nil refs.

    Represents absence of a value (distinct from Empty sentinel).
    """

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from ..values import BoolValue

        return BoolValue(operand)
