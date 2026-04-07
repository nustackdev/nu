"""NoneI - none interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interface import Interface, TypedNu


if TYPE_CHECKING:
    from nu.terms import NoneArg

    from .bool_ import BoolI


__all__ = [
    "NoneI",
]


class NoneI(Interface, TypedNu[None]):
    """None interface. Logical only."""

    def __init__(self, source: object = None) -> None:
        """Default source is None."""
        super().__init__(source)

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: NoneArg) -> BoolI:
        from nu.ops import AndOp

        from .bool_ import BoolI

        return BoolI(AndOp(self, other))

    def or_(self, other: NoneArg) -> BoolI:
        from nu.ops import OrOp

        from .bool_ import BoolI

        return BoolI(OrOp(self, other))

    def not_(self) -> BoolI:
        from nu.ops import NotOp

        from .bool_ import BoolI

        return BoolI(NotOp(self))

    def bool_(self) -> BoolI:
        from nu.ops import BoolOp

        from .bool_ import BoolI

        return BoolI(BoolOp(self))
