"""Base ref class inheriting from every.Ref.

RefBase provides core ergonomics for all typed refs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from every import Gettable, Ref, Sentinel


if TYPE_CHECKING:
    from every import BoolArg, Context, StrArg, Term
    from everybase.py import AnyRef, BoolRef, BytesRef, FloatRef, IntRef, ListRef, StrRef


__all__ = [
    "RefBase",
]


class RefBase[T](Ref[T], ABC):
    """Abstract base for all typed refs.

    Inherits from every.Ref and provides:
    - execute(): delegates to get() if Gettable
    - Special value checks
    - Type conversions
    - Conditional operations

    Subclasses (IntRefBase, etc.) add traits.
    Substrate-specific bases (PyRefBase) add storage.
    """

    @property
    def is_pure(self) -> bool:
        """Check if this ref is pure (no side effects)."""
        return True

    def execute(self, ctx: Context) -> T | Sentinel:
        """Execute this ref by delegating to get()."""
        if isinstance(self, Gettable):
            return self.get(ctx)
        raise NotImplementedError(f"{self.__class__.__name__} must implement get()")

    def resolve(self, ctx: Context) -> object:
        """Resolve to concrete path."""
        return ((self.__class__.__name__,),)

    @abstractmethod
    def get(self, ctx: Context) -> T | Sentinel:
        """Get the value. Implemented by substrate-specific subclasses."""
        ...

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

    def to_bytes(self, encoding: StrArg = "utf-8") -> BytesRef:
        """Convert to bytes."""
        from everybase.morphisms import ToBytesOp
        from everybase.py.bytes import BytesRef

        return BytesRef(ToBytesOp(self, encoding))

    def to_list(self) -> ListRef:
        """Convert to list."""
        from everybase.morphisms import ToListOp
        from everybase.py.list import ListRef

        return ListRef(ToListOp(self))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._source!r})"
