"""Base ref class inheriting from every.Ref.

TypeBase provides core ergonomics for all typed refs:
- Sentinel checks (is_empty, is_invalid, etc.)
- Type conversions (to_int, to_str, etc.)
- Conditional operations (ifelse, or_default)

Substrate-specific bases (PyRef, PVRefBase) implement fetch().
Type-specific bases (IntType, etc.) add operator traits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyabc import BoolArg, Sentinel, Term
    from everybase.values import (
        AnyValue,
        BoolValue,
        BytesValue,
        FloatValue,
        IntValue,
        ListValue,
        StrValue,
    )


__all__ = [
    "TypeBase",
]


class TypeBase[T]:
    """Abstract base for all typed refs.

    Inherits from every.Ref and provides:
    - Ergonomics (sentinel checks, type conversions, conditionals)
    - Abstract fetch() for substrates to implement

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
        from everybase.morphisms import IsEmptyOp
        from everybase.values import BoolValue

        return BoolValue(IsEmptyOp(self))

    def is_invalid(self) -> BoolValue:
        """Check if this value is Invalid."""
        from everybase.morphisms import IsNaNOp
        from everybase.values import BoolValue

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

    # =========================================================================
    # CONDITIONAL OPERATIONS
    # =========================================================================

    def ifelse[ElseT](
        self,
        condition: BoolArg,
        otherwise: ElseT | Term[ElseT | Sentinel],
    ) -> AnyValue:
        """Conditional/ternary: if condition then self else otherwise."""
        from everybase.morphisms import ConditionalOp
        from everybase.values import AnyValue

        return AnyValue(ConditionalOp(self, condition, otherwise))

    def or_default[DefaultT](self, default: DefaultT | Term[DefaultT]) -> AnyValue:
        """Return self if not empty/invalid, otherwise return default."""
        from everybase.values import AnyValue

        return AnyValue(self.ifelse(self.is_sentinel().not_(), default))

    # =========================================================================
    # TYPE CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntValue:
        """Convert to integer."""
        from everybase.morphisms import ToIntOp
        from everybase.values import IntValue

        return IntValue(ToIntOp(self))

    def to_float(self) -> FloatValue:
        """Convert to float."""
        from everybase.morphisms import ToFloatOp
        from everybase.values import FloatValue

        return FloatValue(ToFloatOp(self))

    def to_bool(self) -> BoolValue:
        """Convert to boolean."""
        from everybase.morphisms import ToBoolOp
        from everybase.values import BoolValue

        return BoolValue(ToBoolOp(self))

    def to_str(self) -> StrValue:
        """Convert to string."""
        from everybase.morphisms import ToStrOp
        from everybase.values import StrValue

        return StrValue(ToStrOp(self))

    def to_bytes(self, encoding: str = "utf-8") -> BytesValue:
        """Convert to bytes."""
        from everybase.morphisms import ToBytesOp
        from everybase.values import BytesValue

        return BytesValue(ToBytesOp(self, encoding))

    def to_list(self) -> ListValue:
        """Convert to list."""
        from everybase.morphisms import ToListOp
        from everybase.values import ListValue

        return ListValue(ToListOp(self))
