"""BoolForm - boolean interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Form, TypedNu


if TYPE_CHECKING:
    from nu.terms import BoolArg


__all__ = [
    "BoolForm",
]


class BoolForm(Form, TypedNu[bool]):
    """Boolean interface. Logical + comparable."""

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg) -> BoolForm:
        """Logical AND: self AND other."""
        from nu import And

        return BoolForm(And(self, other))

    def or_(self, other: BoolArg) -> BoolForm:
        """Logical OR: self OR other."""
        from nu import Or

        return BoolForm(Or(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu import Not

        return BoolForm(Not(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu import Bool

        return BoolForm(Bool(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BoolArg) -> BoolForm:
        from nu import Gt

        return BoolForm(Gt(self, other))

    def __lt__(self, other: BoolArg) -> BoolForm:
        from nu import Lt

        return BoolForm(Lt(self, other))

    def __ge__(self, other: BoolArg) -> BoolForm:
        from nu import Ge

        return BoolForm(Ge(self, other))

    def __le__(self, other: BoolArg) -> BoolForm:
        from nu import Le

        return BoolForm(Le(self, other))

    def eq(self, other: BoolArg) -> BoolForm:
        from nu import Eq

        return BoolForm(Eq(self, other))

    def ne(self, other: BoolArg) -> BoolForm:
        from nu import Ne

        return BoolForm(Ne(self, other))

    def is_(self, other: BoolArg) -> BoolForm:
        from nu import IdComp

        return BoolForm(IdComp(self, other))
