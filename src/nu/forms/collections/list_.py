"""List - list interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

from nu.lang import TypedNu

from .abc import MutableSequenceForm
from .abc.sequence_interactions import ListCreate, ListOf


if TYPE_CHECKING:
    from nu.lang import Arg, IntArg, ListArg, Nu

    from ..primitives import (
        Any as AnyForm,
    )
    from ..primitives import (
        Bool,
        Bytes,
        Float,
        Int,
        Str,
    )


__all__ = [
    "List",
]


class List[T](
    MutableSequenceForm[list[T], T, "List[T]", "AnyForm"],
    TypedNu[list[T]],
):
    """List interface. Mutable sequence + comparable."""

    @classmethod
    def create(cls) -> List[T]:
        """Yield a fresh empty list."""
        return cls(ListCreate())

    @classmethod
    def of(cls, *items: Arg) -> List:
        """Yield a list from positional item expressions.

        ``List.of(x, y, z)`` evaluates each argument in the current
        context and packs the results into a fresh list: ``[<x>, <y>, <z>]``.
        Sibling to ``Tuple.of``. An item that resolves to a sentinel
        collapses the whole result to Invalid.
        """
        return cls(ListOf(*items))

    def _wrap_iterable_result(self, operand: Nu) -> List:
        """Wrap operand as List."""
        return List(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> List:
        """Wrap operand as List for slice results."""
        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as an elem-typed Form when known; Any otherwise.

        When the wrapping Form carries an annotation-derived ``TypeInfo`` on
        its payload (i.e. it's a Ref like ``PrimitiveListRef[str]``), dispatch
        the elem to its concrete Form (``Str`` here). Plain value-node
        ``List`` s (no payload) fall back to ``Any`` - the honest
        terminal for value-Form descent without narrowing context.
        """
        ti = self._payload.get("type_info")
        if ti is not None and ti.elem is not None:
            form_cls = ti.elem.to_form()
            return form_cls(operand)  # type: ignore[return-value]
        from ..primitives import Any as AnyForm

        return AnyForm(operand)

    # ---- static overloads: narrow elem type on subscript ----------------
    #
    # Runtime dispatch above; here we tell mypy which concrete Form to
    # expect based on ``T``. Applies to any subclass (PrimitiveListRef[T],
    # nudle refs holding lists, etc.) that specializes ``T``.

    @overload
    def __getitem__(self: List[bool], key: IntArg) -> Bool: ...
    @overload
    def __getitem__(self: List[int], key: IntArg) -> Int: ...
    @overload
    def __getitem__(self: List[float], key: IntArg) -> Float: ...
    @overload
    def __getitem__(self: List[str], key: IntArg) -> Str: ...
    @overload
    def __getitem__(self: List[bytes], key: IntArg) -> Bytes: ...
    @overload
    def __getitem__(self, key: slice) -> List[T]: ...
    @overload
    def __getitem__(self, key: IntArg) -> AnyForm: ...
    def __getitem__(self, key):  # type: ignore[no-untyped-def]
        return super().__getitem__(key)

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: ListArg[T]) -> List[T]:
        from nu.core import Add

        return List(Add(self, other))

    def __radd__(self, other: ListArg[T]) -> List[T]:
        from nu.core import Add

        return List(Add(other, self))

    def __iadd__(self, other: ListArg[T]) -> List[T]:
        """In-place concat: self += other. Mutates and returns self (Action)."""
        from .abc.sequence_interactions import IAdd

        return List(IAdd(self, other))

    def __mul__(self, n: IntArg) -> List[T]:
        """Repeat: self * n -> new list (Query)."""
        from nu.core import Mul

        return List(Mul(self, n))

    def __rmul__(self, n: IntArg) -> List[T]:
        """Repeat: n * self -> new list (Query)."""
        from nu.core import Mul

        return List(Mul(n, self))

    def __imul__(self, n: IntArg) -> List[T]:
        """In-place repeat: self *= n. Mutates and returns self (Action)."""
        from .abc.sequence_interactions import IMul

        return List(IMul(self, n))

    # =========================================================================
    # ITEM ACCESS (mutating)
    # =========================================================================

    def __setitem__(self, index: IntArg, value: Arg[T]) -> Any:  # noqa: ANN401
        """Subscript write: self[index] = value. Mutates; yields nothing (Command)."""
        from .abc.sequence_interactions import SetIndex

        return SetIndex(self, index, value)

    def __delitem__(self, index: IntArg) -> Any:  # noqa: ANN401
        """Subscript delete: del self[index]. Mutates; yields nothing (Command)."""
        from .abc.sequence_interactions import DelIndex

        return DelIndex(self, index)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: ListArg[T]) -> Bool:
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: ListArg[T]) -> Bool:
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: ListArg[T]) -> Bool:
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: ListArg[T]) -> Bool:
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: ListArg[T]) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: ListArg[T]) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: ListArg[T]) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
