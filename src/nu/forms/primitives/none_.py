"""None_ - none interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.lang import NoneArg

    from .bool_ import Bool


__all__ = [
    "None_",
]


class None_(Form, TypedNu[None]):  # noqa: N801
    """None interface. Logical only."""

    def __init__(self, source: object = None) -> None:
        """Default source is None."""
        super().__init__(source)

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: NoneArg) -> Bool:
        """Logical AND: self AND other."""
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: NoneArg) -> Bool:
        """Logical OR: self OR other."""
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT: NOT self."""
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Convert to boolean."""
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))
