"""BoolI - boolean interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interface import Interface


if TYPE_CHECKING:
    from nu.terms import BoolArg


__all__ = [
    "BoolI",
]


class BoolI(Interface[bool]):
    """Boolean interface. Logical + comparable."""

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg) -> BoolI:
        """Logical AND: self AND other."""
        from nu.ops import AndOp

        return BoolI(AndOp(self, other))

    def or_(self, other: BoolArg) -> BoolI:
        """Logical OR: self OR other."""
        from nu.ops import OrOp

        return BoolI(OrOp(self, other))

    def not_(self) -> BoolI:
        """Logical NOT: NOT self."""
        from nu.ops import NotOp

        return BoolI(NotOp(self))

    def bool_(self) -> BoolI:
        """Convert to boolean."""
        from nu.ops import BoolOp

        return BoolI(BoolOp(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BoolArg) -> BoolI:
        from nu.ops import GtOp

        return BoolI(GtOp(self, other))

    def __lt__(self, other: BoolArg) -> BoolI:
        from nu.ops import LtOp

        return BoolI(LtOp(self, other))

    def __ge__(self, other: BoolArg) -> BoolI:
        from nu.ops import GeOp

        return BoolI(GeOp(self, other))

    def __le__(self, other: BoolArg) -> BoolI:
        from nu.ops import LeOp

        return BoolI(LeOp(self, other))

    def eq(self, other: BoolArg) -> BoolI:
        from nu.ops import EqOp

        return BoolI(EqOp(self, other))

    def ne(self, other: BoolArg) -> BoolI:
        from nu.ops import NeOp

        return BoolI(NeOp(self, other))

    def is_(self, other: BoolArg) -> BoolI:
        from nu.ops import IdCompOp

        return BoolI(IdCompOp(self, other))
