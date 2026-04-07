"""Interface - typed wrapper for Nus.

Interface[T] wraps any Nu and provides domain methods (operators, type-specific
methods). It's a construction-time convenience - Interfaces can be shaken from
the tree before execution since they're transparent wrappers.

Hierarchy:
    Nu → RValue → Interface[T]
                   ├── IntI(Interface[int])
                   ├── StrI(Interface[str])
                   └── ...

Interface is also the mixin that Refs inherit to get typed methods.
When inherited by a Ref, __init__ is not called - only the methods matter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Nu, RValue, T_co, Value


if TYPE_CHECKING:
    from nu.context import Context
    from nu.primitives import BoolI


__all__ = [
    "Interface",
]


class Interface(RValue[T_co]):
    """Typed wrapper. Wraps a Nu child, provides domain methods.

    Two modes:
    - Interface(literal) → wraps Value(literal) as child
    - Interface(some_nu) → wraps the Nu as child

    Transparent: execute() delegates to child. Can be shaken from tree.

    Also works as a mixin for Refs - when inherited alongside a Ref,
    __init__ is not called but the methods work because self is a Nu.
    """

    def __init__(self, source: object = None) -> None:
        """Initialize with a literal or Nu source.

        Args:
            source: Python literal (auto-wrapped in Value) or a Nu.
                    None is valid as a literal for NoneI.
        """
        if isinstance(source, Nu):
            super().__init__(source)
        else:
            super().__init__(Value(source))

    @property
    def source(self) -> object:
        """The wrapped source - either a Value or another Nu."""
        return self.children[0] if self.children else None

    async def execute(self, ctx: Context) -> T_co:
        """Delegate to wrapped child."""
        return await self.children[0].execute(ctx)

    @property
    def is_self_pure(self) -> bool:
        """Interface is transparent - purity comes from child."""
        return True

    # =========================================================================
    # SENTINEL CHECKS
    # =========================================================================

    def is_empty(self) -> BoolI:
        """Check if this value is Empty."""
        from nu.ops import IsEmptyOp
        from nu.primitives import BoolI

        return BoolI(IsEmptyOp(self))

    def is_invalid(self) -> BoolI:
        """Check if this value is Invalid."""
        from nu.ops import IsInvalidOp
        from nu.primitives import BoolI

        return BoolI(IsInvalidOp(self))

    def is_sentinel(self) -> BoolI:
        """Check if this value is a special value."""
        return self.is_empty().or_(self.is_invalid())

    def not_empty(self) -> BoolI:
        """Check if this value is not Empty."""
        return self.is_empty().not_()

    def not_invalid(self) -> BoolI:
        """Check if this value is not Invalid."""
        return self.is_invalid().not_()
