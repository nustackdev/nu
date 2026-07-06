"""ListForm - list interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

from nu.lang import TypedNu

from .abc import MutableSequenceForm
from .abc.sequence_interactions import ListCreate


if TYPE_CHECKING:
    from nu.lang import Arg, IntArg, ListArg, Nu

    from ..primitives import (
        AnyForm,
        BoolForm,
        BytesForm,
        FloatForm,
        IntForm,
        StrForm,
    )


__all__ = [
    "ListForm",
]


class ListForm[T](
    MutableSequenceForm[list[T], T, "ListForm[T]", "AnyForm"],
    TypedNu[list[T]],
):
    """ListQuery interface. Mutable sequence + comparable."""

    @classmethod
    def create(cls) -> ListForm[T]:
        """Yield a fresh empty list."""
        return cls(ListCreate())

    def _wrap_iterable_result(self, operand: Nu) -> ListForm:
        """Wrap operand as ListForm."""
        return ListForm(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListForm:
        """Wrap operand as ListForm for slice results."""
        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as an elem-typed Form when known; AnyForm otherwise.

        When the wrapping Form carries an annotation-derived ``TypeInfo`` on
        its payload (i.e. it's a Ref like ``PrimitiveListRef[str]``), dispatch
        the elem to its concrete Form (``StrForm`` here). Plain value-node
        ``ListForm`` s (no payload) fall back to ``AnyForm`` - the honest
        terminal for value-Form descent without narrowing context.
        """
        ti = self._payload.get("type_info")
        if ti is not None and ti.elem is not None:
            form_cls = ti.elem.to_form()
            return form_cls(operand)  # type: ignore[return-value]
        from ..primitives import AnyForm

        return AnyForm(operand)

    # ---- static overloads: narrow elem type on subscript ----------------
    #
    # Runtime dispatch above; here we tell mypy which concrete Form to
    # expect based on ``T``. Applies to any subclass (PrimitiveListRef[T],
    # nudle refs holding lists, etc.) that specializes ``T``.

    @overload
    def __getitem__(self: ListForm[bool], key: IntArg) -> BoolForm: ...
    @overload
    def __getitem__(self: ListForm[int], key: IntArg) -> IntForm: ...
    @overload
    def __getitem__(self: ListForm[float], key: IntArg) -> FloatForm: ...
    @overload
    def __getitem__(self: ListForm[str], key: IntArg) -> StrForm: ...
    @overload
    def __getitem__(self: ListForm[bytes], key: IntArg) -> BytesForm: ...
    @overload
    def __getitem__(self, key: slice) -> ListForm[T]: ...
    @overload
    def __getitem__(self, key: IntArg) -> AnyForm: ...
    def __getitem__(self, key):  # type: ignore[no-untyped-def]
        return super().__getitem__(key)

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: ListArg[T]) -> ListForm[T]:
        from nu.core import AddQuery

        return ListForm(AddQuery(self, other))

    def __radd__(self, other: ListArg[T]) -> ListForm[T]:
        from nu.core import AddQuery

        return ListForm(AddQuery(other, self))

    def __iadd__(self, other: ListArg[T]) -> ListForm[T]:
        """In-place concat: self += other. Mutates and returns self (Action)."""
        from .abc.sequence_interactions import IAddAction

        return ListForm(IAddAction(self, other))

    def __mul__(self, n: IntArg) -> ListForm[T]:
        """Repeat: self * n -> new list (Query)."""
        from nu.core import MulQuery

        return ListForm(MulQuery(self, n))

    def __rmul__(self, n: IntArg) -> ListForm[T]:
        """Repeat: n * self -> new list (Query)."""
        from nu.core import MulQuery

        return ListForm(MulQuery(n, self))

    def __imul__(self, n: IntArg) -> ListForm[T]:
        """In-place repeat: self *= n. Mutates and returns self (Action)."""
        from .abc.sequence_interactions import IMulAction

        return ListForm(IMulAction(self, n))

    # =========================================================================
    # ITEM ACCESS (mutating)
    # =========================================================================

    def __setitem__(self, index: IntArg, value: Arg[T]) -> Any:  # noqa: ANN401
        """Subscript write: self[index] = value. Mutates; yields nothing (Command)."""
        from .abc.sequence_interactions import SetIndexCommand

        return SetIndexCommand(self, index, value)

    def __delitem__(self, index: IntArg) -> Any:  # noqa: ANN401
        """Subscript delete: del self[index]. Mutates; yields nothing (Command)."""
        from .abc.sequence_interactions import DelIndexCommand

        return DelIndexCommand(self, index)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: ListArg[T]) -> BoolForm:
        from nu.core import GtQuery

        from ..primitives import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: ListArg[T]) -> BoolForm:
        from nu.core import LtQuery

        from ..primitives import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: ListArg[T]) -> BoolForm:
        from nu.core import GeQuery

        from ..primitives import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: ListArg[T]) -> BoolForm:
        from nu.core import LeQuery

        from ..primitives import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: ListArg[T]) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from ..primitives import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: ListArg[T]) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from ..primitives import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: ListArg[T]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from ..primitives import BoolForm

        return BoolForm(IsQuery(self, other))
