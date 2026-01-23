"""Base ref class inheriting from every.Ref.

RefBase provides core ergonomics for all typed refs:
- Sentinel checks (is_empty, is_invalid, etc.)
- Type conversions (to_int, to_str, etc.)
- Conditional operations (ifelse, or_default)

Substrate-specific bases (PyRef, PVRefBase) implement fetch().
Type-specific bases (IntRefBase, etc.) add operator traits.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from every import Ref, Sentinel


if TYPE_CHECKING:
    from every import BoolArg, Context, Term
    from everybase.py import AnyRef, BoolRef, BytesRef, FloatRef, IntRef, ListRef, StrRef


__all__ = [
    "RefBase",
]


class RefBase[T](Ref[T], ABC):
    """Abstract base for all typed refs.

    Inherits from every.Ref and provides:
    - Ergonomics (sentinel checks, type conversions, conditionals)
    - Abstract fetch() for substrates to implement

    Subclasses (IntRefBase, etc.) add operator traits.
    Substrate-specific bases (PyRef, PVRefBase) add storage.

    Note: Arithmetic operations return Python memory refs because
    the result is a computation (lazy expression), not a storage
    location. A PVIntRef + 5 produces IntRef(AddOp(...)).
    """

    @abstractmethod
    def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch the value from this location.

        Implemented by substrate-specific subclasses to actually
        retrieve the value from storage (memory, disk, network, etc.).

        Args:
            ctx: Execution context

        Returns:
            The value, or Sentinel if absent/invalid
        """
        ...

    def resolve(self, ctx: Context) -> object:
        """Resolve to identity/location.

        Default implementation returns minimal identifier.
        Path-based substrates override with full path construction.

        Args:
            ctx: Execution context

        Returns:
            Location identifier
        """
        return (self.__class__.__name__,)

    # =========================================================================
    # SPECIAL VALUE CHECKS
    # =========================================================================

    def is_empty(self) -> BoolRef:
        """Check if this value is Empty."""
        from everybase.morphisms import IsEmptyOp
        from everybase.py.bool import BoolRef

        return BoolRef(IsEmptyOp(self))

    def is_invalid(self) -> BoolRef:
        """Check if this value is Invalid."""
        from everybase.morphisms import IsNaNOp
        from everybase.py.bool import BoolRef

        return BoolRef(IsNaNOp(self))

    def is_sentinel(self) -> BoolRef:
        """Check if this value is a special value."""
        return self.is_empty().or_(self.is_invalid())

    def not_empty(self) -> BoolRef:
        """Check if this value is not Empty."""
        return self.is_empty().not_()

    def not_invalid(self) -> BoolRef:
        """Check if this value is not Invalid."""
        return self.is_invalid().not_()

    # =========================================================================
    # CONDITIONAL OPERATIONS
    # =========================================================================

    def ifelse[ElseT](
        self,
        condition: BoolArg,
        otherwise: ElseT | Term[ElseT | Sentinel],
    ) -> AnyRef:
        """Conditional/ternary: if condition then self else otherwise."""
        from everybase.morphisms import ConditionalOp
        from everybase.py.any import AnyRef

        return AnyRef(ConditionalOp(self, condition, otherwise))

    def or_default[DefaultT](self, default: DefaultT | Term[DefaultT]) -> AnyRef:
        """Return self if not empty/invalid, otherwise return default."""
        from everybase.py.any import AnyRef

        return AnyRef(self.ifelse(self.is_sentinel().not_(), default))

    # =========================================================================
    # TYPE CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntRef:
        """Convert to integer."""
        from everybase.morphisms import ToIntOp
        from everybase.py.int import IntRef

        return IntRef(ToIntOp(self))

    def to_float(self) -> FloatRef:
        """Convert to float."""
        from everybase.morphisms import ToFloatOp
        from everybase.py.float import FloatRef

        return FloatRef(ToFloatOp(self))

    def to_bool(self) -> BoolRef:
        """Convert to boolean."""
        from everybase.morphisms import ToBoolOp
        from everybase.py.bool import BoolRef

        return BoolRef(ToBoolOp(self))

    def to_str(self) -> StrRef:
        """Convert to string."""
        from everybase.morphisms import ToStrOp
        from everybase.py.str import StrRef

        return StrRef(ToStrOp(self))

    def to_bytes(self, encoding: str = "utf-8") -> BytesRef:
        """Convert to bytes."""
        from everybase.morphisms import ToBytesOp
        from everybase.py.bytes import BytesRef

        return BytesRef(ToBytesOp(self, encoding))

    def to_list(self) -> ListRef:
        """Convert to list."""
        from everybase.morphisms import ToListOp
        from everybase.py.list import ListRef

        return ListRef(ToListOp(self))
