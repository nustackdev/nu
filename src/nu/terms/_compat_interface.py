"""Interface and TypedNu - the two faces of Nu's type system.

Interface is the abstract base for all typed interfaces. Provides shared
methods (sentinel checks) that work on any Nu. ABCs like MappingI,
ContainerI, SizedI inherit Interface to get these methods.

TypedNu[T] is the concrete wrapper that makes a class a Nu node. Takes
a Nu or literal, wraps it as a child, forwards the child's stream. Leaf
interfaces (IntI, DictI, StrI, etc) inherit both Interface and TypedNu
so they can participate as Nu tree nodes: `DictI(some_op).keys()`.

Hierarchy:
    Interface                       abstract base (sentinel checks, no type param)
        ContainerI, SizedI, ...     zero-level ABCs inherit Interface directly
        MappingI, SequenceI, ...    higher ABCs get Interface through MRO

    RValue -> TypedNu[T]            concrete wrapper (Nu node in tree)

    IntI(Interface, TypedNu[int])          primitive leaf: contract + wrapper
    DictI(MutableMappingI, TypedNu[dict])  collection leaf: gets Interface through MRO

Later rename: Interface -> Form (the fourth Nu kind in the taxonomy).
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING

from ._compat_nu import RValue
from ._compat_types import T_co


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context
    from ..primitives import BoolI


__all__ = [
    "Interface",
    "TypedNu",
]


class Interface:
    """Abstract base for all typed interfaces.

    Provides shared methods (sentinel checks) that work on any Nu. Does NOT
    make the class a Nu node - that's TypedNu's job. No type parameter -
    sentinel checks don't depend on the wrapped type.

    ABCs (MappingI, ContainerI, etc) inherit Interface for the contract.
    Leaf interfaces (IntI, DictI, etc) inherit both Interface + TypedNu.
    """

    # =========================================================================
    # SENTINEL CHECKS
    # =========================================================================

    def is_empty(self) -> BoolI:
        from nu.interactions import IsEmpty
        from nu.primitives import BoolI

        return BoolI(IsEmpty(self))

    def is_invalid(self) -> BoolI:
        from nu.interactions import IsInvalid
        from nu.primitives import BoolI

        return BoolI(IsInvalid(self))

    def is_sentinel(self) -> BoolI:
        return self.is_empty().or_(self.is_invalid())

    def not_empty(self) -> BoolI:
        return self.is_empty().not_()

    def not_invalid(self) -> BoolI:
        return self.is_invalid().not_()


class TypedNu(RValue[T_co]):
    """Concrete Nu wrapper - makes a class a node in the Nu tree.

    Takes a Nu or literal, wraps it as a child, forwards the child's stream.
    Transparent: can be shaken from the tree before execution.

    Leaf interfaces (IntI, DictI, etc) inherit this alongside Interface so
    they can participate in Nu tree construction:
        IntI(Add(a, b)) + 1  ->  Add(IntI(Add(a, b)), Literal(1))
    """

    def __init__(self, source: object = None, *args: object) -> None:
        super().__init__(source, *args)

    @property
    def source(self) -> object:
        return self.children[0] if self.children else None

    async def aopen(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        async with aclosing(self.children[0].aopen(ctx)) as gen:
            async for v in gen:
                yield v

    def open(self, ctx: Context) -> Generator[T_co, None, None]:
        with closing(self.children[0].open(ctx)) as gen:
            yield from gen

    @property
    def is_self_pure(self) -> bool:
        return True
