"""NoneForm - none interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Form, TypedNu


if TYPE_CHECKING:
    from nu.terms import NoneArg

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
        from nu import And

        from .bool_ import BoolForm

        return BoolForm(And(self, other))

    def or_(self, other: NoneArg) -> BoolForm:
        from nu import Or

        from .bool_ import BoolForm

        return BoolForm(Or(self, other))

    def not_(self) -> BoolForm:
        from nu import Not

        from .bool_ import BoolForm

        return BoolForm(Not(self))

    def bool_(self) -> BoolForm:
        from nu import Bool

        from .bool_ import BoolForm

        return BoolForm(Bool(self))
