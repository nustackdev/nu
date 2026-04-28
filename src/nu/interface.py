"""Interface and TypedNu - the type-wrapping layer.

`Interface` is an ABC that contributes shared methods (sentinel checks)
to typed interfaces. ABCs like MappingI, ContainerI, SizedI inherit
Interface to get these methods.

`TypedNu[T]` is a transparent ScalarQuery wrapper: it wraps a Nu child
(or literal) and passes the child's value through. Leaf interfaces like
IntI, DictI, StrI inherit both Interface and TypedNu so they can
participate as Nu tree nodes:

    IntI(Add(a, b)) + 1  ->  Add(IntI(Add(a, b)), Literal(1))

Hierarchy:
    Interface                       abstract base (sentinel checks)
        ContainerI, SizedI, ...     zero-level ABCs
        MappingI, SequenceI, ...    higher ABCs

    TypedNu[T]                      ScalarQuery passthrough
    IntI(Interface, TypedNu[int])   primitive leaf
    DictI(MutableMappingI, TypedNu[dict])  collection leaf
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Generic

from .terms.query import ScalarQuery
from .terms.types import Mode, T_co


if TYPE_CHECKING:
    from .primitives import BoolI


__all__ = [
    "Interface",
    "TypedNu",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Interface:
    """ABC for typed interfaces. Contributes sentinel-check helpers."""

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


class TypedNu(ScalarQuery, Generic[T_co]):
    """Transparent ScalarQuery passthrough. Carries a python type tag T.

    Wraps a single Nu (or literal). Operand recursion + sentinel
    propagation happen in `ScalarQuery.eval`/`aeval`; `_apply` returns
    the operand unchanged.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = False

    def __init__(self, source: object = None) -> None:
        super().__init__(source)

    @property
    def source(self) -> Any:  # noqa: ANN401
        return self._children[0] if self._children else None

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0]
