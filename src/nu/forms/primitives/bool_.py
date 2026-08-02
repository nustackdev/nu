"""Bool - boolean interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.lang import BoolArg


__all__ = [
    "Bool",
]


class Bool(Form, TypedNu[bool]):
    """Boolean interface. Logical + comparable."""

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg) -> Bool:
        """Logical AND: self AND other."""
        from nu.core import And

        return Bool(And(self, other))

    def or_(self, other: BoolArg) -> Bool:
        """Logical OR: self OR other."""
        from nu.core import Or

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT: NOT self."""
        from nu.core import Not

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Convert to boolean."""
        from nu.core import ToBool

        return Bool(ToBool(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BoolArg) -> Bool:
        from nu.core import Gt

        return Bool(Gt(self, other))

    def __lt__(self, other: BoolArg) -> Bool:
        from nu.core import Lt

        return Bool(Lt(self, other))

    def __ge__(self, other: BoolArg) -> Bool:
        from nu.core import Ge

        return Bool(Ge(self, other))

    def __le__(self, other: BoolArg) -> Bool:
        from nu.core import Le

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: BoolArg) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        return Bool(Eq(self, other))

    def __ne__(self, other: BoolArg) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        return Bool(Ne(self, other))

    def is_(self, other: BoolArg) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        return Bool(Is(self, other))
