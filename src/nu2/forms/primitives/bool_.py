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
        from nu2.core import AndQuery

        return BoolForm(AndQuery(self, other))

    def or_(self, other: BoolArg) -> BoolForm:
        """Logical OR: self OR other."""
        from nu2.core import OrQuery

        return BoolForm(OrQuery(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu2.core import NotQuery

        return BoolForm(NotQuery(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu2.core import BoolQuery

        return BoolForm(BoolQuery(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BoolArg) -> BoolForm:
        from nu2.core import GtQuery

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: BoolArg) -> BoolForm:
        from nu2.core import LtQuery

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: BoolArg) -> BoolForm:
        from nu2.core import GeQuery

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: BoolArg) -> BoolForm:
        from nu2.core import LeQuery

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: BoolArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import EqQuery

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: BoolArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import NeQuery

        return BoolForm(NeQuery(self, other))

    def is_(self, other: BoolArg) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import IsQuery

        return BoolForm(IsQuery(self, other))
