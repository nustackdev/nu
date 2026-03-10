"""ObjectType — universal base for all everybase types.

ObjectType provides term-algebra methods shared by ALL types:
- Sentinel checks (is_empty, is_invalid, etc.)

This is the root of the type hierarchy. TypeBase inherits from ObjectType
and adds everybase-specific kernel identity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..values import BoolValue


__all__ = [
    "ObjectType",
]


class ObjectType:
    """Universal base for all everybase types.

    Provides term-algebra methods that every type shares:
    - Sentinel checks (is_empty, is_invalid, is_sentinel, not_empty, not_invalid)
    """

    # =========================================================================
    # SPECIAL VALUE CHECKS
    # =========================================================================

    def is_empty(self) -> BoolValue:
        """Check if this value is Empty."""
        from ..morphisms import IsEmptyOp
        from ..values import BoolValue

        return BoolValue(IsEmptyOp(self))

    def is_invalid(self) -> BoolValue:
        """Check if this value is Invalid."""
        from ..morphisms import IsNaNOp
        from ..values import BoolValue

        return BoolValue(IsNaNOp(self))

    def is_sentinel(self) -> BoolValue:
        """Check if this value is a special value."""
        return self.is_empty().or_(self.is_invalid())

    def not_empty(self) -> BoolValue:
        """Check if this value is not Empty."""
        return self.is_empty().not_()

    def not_invalid(self) -> BoolValue:
        """Check if this value is not Invalid."""
        return self.is_invalid().not_()
