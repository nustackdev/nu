"""Boolean ref base combining logical traits.

BoolRefBase = RefBase[bool] + Logical + Comparable
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everybase.traits import Comparable, Logical

from .base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef


__all__ = [
    "BoolRefBase",
]


class BoolRefBase(
    Logical["bool | BoolRef", "BoolRef"],
    Comparable["bool | BoolRef"],
    RefBase[bool],
    ABC,
):
    """Abstract base for boolean refs.

    Combines:
    - Logical: and_(), or_(), not_(), bool_()
    - Comparable: >, <, >=, <=, eq(), ne(), is_()

    Concrete implementations must add get() for their storage substrate.
    """

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)
