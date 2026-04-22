"""NoneI - none interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Interface, TypedNu


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
        from nu.interactions import And

        from .bool_ import BoolI

        return BoolI(And(self, other))

    def or_(self, other: NoneArg) -> BoolI:
        from nu.interactions import Or

        from .bool_ import BoolI

        return BoolI(Or(self, other))

    def not_(self) -> BoolI:
        from nu.interactions import Not

        from .bool_ import BoolI

        return BoolI(Not(self))

    def bool_(self) -> BoolI:
        from nu.interactions import Bool

        from .bool_ import BoolI

        return BoolI(Bool(self))
