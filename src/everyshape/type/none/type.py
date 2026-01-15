"""None/Nil type for Term expressions.

This module provides NilType which represents None expressions (literal or computed).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.term.type import LogicalBase, Type


if TYPE_CHECKING:
    from everyshape.term.term import Term
    from everyshape.typing import Sentinel

    from ..bool.type import BoolType  # noqa: F401


__all__ = [
    "NilType",
]


class NilType(
    LogicalBase["None | NilType", "BoolType"],
    Type[None],
):
    """Nil type - represents None expressions (literal or computed).

    Example:
        >>> x = NilType()
        >>> x.is_empty()  # Returns BoolType
    """

    def __init__(self, source: None | Term[None] | Sentinel = None) -> None:
        """Init."""
        """Initialize Nil type (defaults to None literal)."""
        super().__init__(source if source is not None else None)

    def _wrap_logical_result(self, operand: Term) -> Term:
        from ..bool.type import BoolType

        return BoolType(operand)
