"""NoneForm - none interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu2.lang import NoneArg

    from .bool_ import BoolForm


__all__ = [
    "NoneForm",
]


class NoneForm(Form, TypedNu[None]):
    """None interface. Logical only."""

    def __init__(self, source: object = None) -> None:
        """Default source is None."""
        super().__init__(source)

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: NoneArg) -> BoolForm:
        """Logical AND: self AND other."""
        from nu2.core import AndQuery

        from .bool_ import BoolForm

        return BoolForm(AndQuery(self, other))

    def or_(self, other: NoneArg) -> BoolForm:
        """Logical OR: self OR other."""
        from nu2.core import OrQuery

        from .bool_ import BoolForm

        return BoolForm(OrQuery(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu2.core import NotQuery

        from .bool_ import BoolForm

        return BoolForm(NotQuery(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu2.core import BoolQuery

        from .bool_ import BoolForm

        return BoolForm(BoolQuery(self))
