"""BoolI - boolean interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from nu.terms import BoolArg


__all__ = [
    "BoolI",
]


class BoolI(Interface, TypedNu[bool]):
    """Boolean interface. Logical + comparable."""

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg) -> BoolI:
        """Logical AND: self AND other."""
        from nu import And

        return BoolI(And(self, other))

    def or_(self, other: BoolArg) -> BoolI:
        """Logical OR: self OR other."""
        from nu import Or

        return BoolI(Or(self, other))

    def not_(self) -> BoolI:
        """Logical NOT: NOT self."""
        from nu import Not

        return BoolI(Not(self))

    def bool_(self) -> BoolI:
        """Convert to boolean."""
        from nu import Bool

        return BoolI(Bool(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BoolArg) -> BoolI:
        from nu import Gt

        return BoolI(Gt(self, other))

    def __lt__(self, other: BoolArg) -> BoolI:
        from nu import Lt

        return BoolI(Lt(self, other))

    def __ge__(self, other: BoolArg) -> BoolI:
        from nu import Ge

        return BoolI(Ge(self, other))

    def __le__(self, other: BoolArg) -> BoolI:
        from nu import Le

        return BoolI(Le(self, other))

    def eq(self, other: BoolArg) -> BoolI:
        from nu import Eq

        return BoolI(Eq(self, other))

    def ne(self, other: BoolArg) -> BoolI:
        from nu import Ne

        return BoolI(Ne(self, other))

    def is_(self, other: BoolArg) -> BoolI:
        from nu import IdComp

        return BoolI(IdComp(self, other))
