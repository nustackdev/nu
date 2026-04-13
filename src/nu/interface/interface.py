"""Interface and TypedNu - the two faces of Nu's type system.

Interface[T] is the abstract base for all typed interfaces. It provides
shared methods (sentinel checks) that work on any Nu. ABCs like MappingI,
ContainerI, SizedI inherit Interface to get these methods.

TypedNu[T] is the concrete wrapper that makes a class a Nu node. It takes
a Nu or literal, wraps it as a child, and delegates execute() to it.
Leaf interfaces (IntI, DictI, StrI, etc) inherit both Interface and TypedNu
so they can be used as Nu tree nodes: DictI(some_op).keys().

Hierarchy:
    Interface                       abstract base (sentinel checks, no type param)
        ContainerI, SizedI, ...     zero-level ABCs inherit Interface directly
        MappingI, SequenceI, ...    higher ABCs get Interface through MRO

    RValue → TypedNu[T]            concrete wrapper (Nu node in tree)

    IntI(Interface, TypedNu[int])          primitive leaf: contract + wrapper
    DictI(MutableMappingI, TypedNu[dict])  collection leaf: gets Interface through abc chain
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Literal, Nu, RValue
from nu.terms.type_vars import T_co


if TYPE_CHECKING:
    from nu.context import Context
    from nu.primitives import BoolI


__all__ = [
    "Interface",
    "TypedNu",
]


class Interface:
    """Abstract base for all typed interfaces.

    Provides shared methods (sentinel checks) that work on any Nu.
    Does NOT make the class a Nu node - that's TypedNu's job.
    No type parameter - sentinel checks don't depend on the wrapped type.

    ABCs (MappingI, ContainerI, etc) inherit Interface for the contract.
    Leaf interfaces (IntI, DictI, etc) inherit both Interface + TypedNu.
    """

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


class TypedNu(RValue[T_co]):
    """Concrete Nu wrapper - makes a class a node in the Nu tree.

    Takes a Nu or literal, wraps it as a child, delegates execute() to it.
    Transparent: can be shaken from the tree before execution.

    Leaf interfaces (IntI, DictI, etc) inherit this alongside Interface
    so they can participate in Nu tree construction:
        IntI(AddOp(a, b)) + 1  →  AddOp(IntI(AddOp(a, b)), Literal(1))
    """

    def __init__(self, source: object = None, *args: object) -> None:
        """Initialize with a literal or Nu source.

        Args:
            source: Python literal (auto-wrapped in Literal) or a Nu.
                    None is valid as a literal for NoneI.
            *args: Extra positional args forwarded through cooperative MRO
                   (e.g. parent ref passed by shapes.Ref.__init__).
        """
        if isinstance(source, Nu):
            super().__init__(source, *args)
        else:
            super().__init__(Literal(source), *args)

    @property
    def source(self) -> object:
        """The wrapped source - either a Literal or another Nu."""
        return self.children[0] if self.children else None

    async def execute(self, ctx: Context) -> T_co:
        """Delegate to wrapped child."""
        return await self.children[0].execute(ctx)

    @property
    def is_self_pure(self) -> bool:
        """TypedNu is transparent - purity comes from child."""
        return True
