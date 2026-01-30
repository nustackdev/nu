"""None ref base for nil/null values.

NoneRefBase = RefBase[None] + Logical

Returns concrete py types.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everybase.capabilities import Logical

from .base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef, NoneRef  # noqa: F401


__all__ = [
    "NoneRefBase",
]


class NoneRefBase(
    Logical["None | NoneRef", "BoolRef"],
    RefBase[None],
    ABC,
):
    """Abstract base for None/nil refs.

    Represents absence of a value (distinct from Empty sentinel).
    """

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)
