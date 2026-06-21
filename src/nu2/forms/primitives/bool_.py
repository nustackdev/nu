"""BoolForm - boolean interface.

v1 reference: ``src/nu/forms/primitives/bool_.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu2.lang import BoolArg


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
        from nu2.core import And

        return BoolForm(And(self, other))

    def or_(self, other: BoolArg) -> BoolForm:
        """Logical OR: self OR other."""
        from nu2.core import Or

        return BoolForm(Or(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu2.core import Not

        return BoolForm(Not(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu2.core import Bool

        return BoolForm(Bool(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BoolArg) -> BoolForm:
        from nu2.core import Gt

        return BoolForm(Gt(self, other))

    def __lt__(self, other: BoolArg) -> BoolForm:
        from nu2.core import Lt

        return BoolForm(Lt(self, other))

    def __ge__(self, other: BoolArg) -> BoolForm:
        from nu2.core import Ge

        return BoolForm(Ge(self, other))

    def __le__(self, other: BoolArg) -> BoolForm:
        from nu2.core import Le

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: BoolArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import Eq

        return BoolForm(Eq(self, other))

    def __ne__(self, other: BoolArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import Ne

        return BoolForm(Ne(self, other))

    def is_(self, other: BoolArg) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import Is

        return BoolForm(Is(self, other))
