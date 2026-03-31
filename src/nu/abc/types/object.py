"""Object — universal base for all everybase types.

Object[T] is the root of the type hierarchy, providing:
- Generic type parameter [T] for type safety
- Sentinel checks (is_empty, is_invalid, etc.)

Substrate-specific bases (PyRef, PVRefBase) implement fetch().
Type-specific bases (IntType, etc.) add operator traits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..values import BoolValue


__all__ = [
    "Object",
]


class Object[T]:
    """Universal base for all everybase types.

    Provides:
    - Generic type parameter [T] for type safety
    - Sentinel checks (is_empty, is_invalid, is_sentinel, not_empty, not_invalid)

    Subclasses (IntType, etc.) add operator traits.
    Substrate-specific bases (PyRef, PVRefBase) add storage.

    Note: Arithmetic operations return Python memory refs because
    the result is a computation (lazy expression), not a storage
    location. A PVIntRef + 5 produces IntValue(AddOp(...)).
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
