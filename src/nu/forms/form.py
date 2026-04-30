"""Form and TypedNu - the type-wrapping layer.

`Form` is an ABC that contributes shared methods (sentinel checks)
to typed interfaces. ABCs like MappingForm, ContainerForm, SizedForm inherit
Form to get these methods.

`TypedNu[T]` is a transparent ScalarQuery wrapper: it wraps a Nu child
(or literal) and passes the child's value through. Leaf interfaces like
IntForm, DictForm, StrForm inherit both Form and TypedNu so they can
participate as Nu tree nodes:

    IntForm(Add(a, b)) + 1  ->  Add(IntForm(Add(a, b)), Literal(1))

Hierarchy:
    Form                       abstract base (sentinel checks)
        ContainerForm, SizedForm, ...     zero-level ABCs
        MappingForm, SequenceForm, ...    higher ABCs

    TypedNu[T]                      ScalarQuery passthrough
    IntForm(Form, TypedNu[int])   primitive leaf
    DictForm(MutableMappingForm, TypedNu[dict])  collection leaf
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Generic

from ..terms.query import ScalarQuery
from ..terms.types import Mode, T_co


if TYPE_CHECKING:
    from .primitives import BoolForm


__all__ = [
    "Form",
    "TypedNu",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Form:
    """ABC for typed interfaces. Contributes sentinel-check helpers."""

    def is_empty(self) -> BoolForm:
        from nu import IsEmpty
        from nu.forms.primitives import BoolForm

        return BoolForm(IsEmpty(self))

    def is_invalid(self) -> BoolForm:
        from nu import IsInvalid
        from nu.forms.primitives import BoolForm

        return BoolForm(IsInvalid(self))

    def is_sentinel(self) -> BoolForm:
        return self.is_empty().or_(self.is_invalid())

    def not_empty(self) -> BoolForm:
        return self.is_empty().not_()

    def not_invalid(self) -> BoolForm:
        return self.is_invalid().not_()


class TypedNu(ScalarQuery, Generic[T_co]):
    """Transparent ScalarQuery passthrough. Carries a python type tag T.

    Wraps a single Nu (or literal). Operand recursion + sentinel
    propagation happen in `ScalarQuery.eval`/`aeval`; `_apply` returns
    the operand unchanged.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = False

    def __init__(self, *children: object) -> None:
        super().__init__(*children)

    @property
    def source(self) -> Any:  # noqa: ANN401
        return self._children[0] if self._children else None

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0]
