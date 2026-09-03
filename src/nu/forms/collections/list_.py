"""List - list interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

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


T = TypeVar("T")


class List(
    MutableSequenceForm[list[T], T, "List[T]", "AnyForm"],
    TypedNu[list[T]],
    Generic[T],
):
    """List interface. Mutable sequence + comparable.

    Notes:
        - `+` concatenates and `*` repeats, matching Python's list
          operators. There's no other arithmetic.
        - Comparison operators compare element-by-element, Python list
          ordering, and yield Bool. Chained comparisons like `a > b > c`
          do not build a single term; write them as `And(a > b, b > c)`.
        - Indexing with an out-of-range int raises at evaluation time,
          matching Python. Slicing never raises; out-of-range bounds clamp
          like Python slicing.
        - Subscript write/delete (`self[i] = v`, `del self[i]`) mutate in
          place and need a Ref on the left, not a plain List value - they
          can't run standalone.

    Example:
        >>> nu.run(nu.List.of(1, 2) + nu.List.of(3, 4))[0]
        [1, 2, 3, 4]
    """

    @classmethod
    def create(cls) -> List[T]:
        """Yield a fresh empty list.

        Yields:
            An empty list.

        Example:
            >>> nu.run(nu.List.create())[0]
            []
        """
        return cls(ListCreate())

    @classmethod
    def of(cls, *items: Arg) -> List:
        """Yield a list from positional item expressions.

        Args:
            items: the item expressions, packed into the list in order.
                Each may be a Nu expression or a plain literal.

        Notes:
            - Sibling to `Tuple.of`, same evaluation shape, different
              wrapping.

        Yields:
            The list `[<items[0]>, <items[1]>, ...]`. INVALID when any item
            resolves to a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3))[0]
            [1, 2, 3]
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

        Notes:
            - When the wrapping Form carries an annotation-derived
              `TypeInfo` on its payload (i.e. it's a Ref like
              `PrimitiveListRef[str]`), dispatch the elem to its concrete
              Form (`Str` here).
            - Plain value-node `List`s (no payload) fall back to `Any` -
              the honest terminal for value-Form descent without
              narrowing context.
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
        """Element at an int index, or subsequence for a slice.

        Args:
            key: an int index, or a Python slice of int start/stop/step.

        Notes:
            - An out-of-range int index raises at evaluation time,
              matching Python. A slice never raises; out-of-range bounds
              clamp like Python slicing.
            - Negative indices and negative slice bounds work as in
              Python.
            - When `T` is a known primitive (`bool`, `int`, `float`,
              `str`, `bytes`), the overloads above narrow the int-index
              result to that Form's type for the type checker; anything
              else falls back to `Any`.

        Yields:
            The element for an int key, the sublist for a slice. INVALID
            when self is a sentinel or not a List.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3)[1])[0]
            2

            >>> nu.run(nu.List.of(1, 2, 3)[1:3])[0]
            [2, 3]
        """
        return super().__getitem__(key)

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: ListArg[T]) -> List[T]:
        """Concatenation of self and other.

        Args:
            other: the list to append to self.

        Yields:
            The concatenation. INVALID when either operand is not a List or
            is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2) + nu.List.of(3, 4))[0]
            [1, 2, 3, 4]
        """
        from nu.core import Add

        return List(Add(self, other))

    def __radd__(self, other: ListArg[T]) -> List[T]:
        """Concatenation of other and self, with self on the right.

        Args:
            other: the list on the left of the `+`.

        Notes:
            - Reached only when the left operand is a plain Python list. A
              Nu List on the left goes through its own `__add__` first and
              never lands here.

        Yields:
            The concatenation. INVALID when either operand is not a List or
            is a sentinel.

        Example:
            >>> nu.run([1, 2] + nu.List.of(3, 4))[0]
            [1, 2, 3, 4]
        """
        from nu.core import Add

        return List(Add(other, self))

    def __iadd__(self, other: ListArg[T]) -> List[T]:
        """In-place concatenation: self += other.

        Args:
            other: the list to append to self, in place.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain List value.

        Yields:
            self, after the mutation (Action).
        """
        from .abc.sequence_interactions import IAdd

        return List(IAdd(self, other))

    def __mul__(self, n: IntArg) -> List[T]:
        """Self repeated n times.

        Args:
            n: the repeat count. `0` or negative yields an empty list.

        Yields:
            The repeated list. INVALID when self is a sentinel or not a
            List.

        Example:
            >>> nu.run(nu.List.of(1, 2) * 3)[0]
            [1, 2, 1, 2, 1, 2]
        """
        from nu.core import Mul

        return List(Mul(self, n))

    def __rmul__(self, n: IntArg) -> List[T]:
        """Self repeated n times, with self on the right of the `*`.

        Args:
            n: the repeat count, on the left of the `*`.

        Notes:
            - Reached only when the left operand is a plain Python int. A
              Nu Int on the left goes through `__mul__` instead.

        Yields:
            The repeated list. INVALID when self is a sentinel or not a
            List.

        Example:
            >>> nu.run(3 * nu.List.of(1, 2))[0]
            [1, 2, 1, 2, 1, 2]
        """
        from nu.core import Mul

        return List(Mul(n, self))

    def __imul__(self, n: IntArg) -> List[T]:
        """In-place repeat: self *= n.

        Args:
            n: the repeat count. `0` or negative empties self.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain List value.

        Yields:
            self, after the mutation (Action).
        """
        from .abc.sequence_interactions import IMul

        return List(IMul(self, n))

    # =========================================================================
    # ITEM ACCESS (mutating)
    # =========================================================================

    def __setitem__(self, index: IntArg, value: Arg[T]) -> Any:  # noqa: ANN401
        """Subscript write: self[index] = value.

        Args:
            index: the position to write to. An out-of-range index raises
                at evaluation time, matching Python.
            value: the value to store at index.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain List value.

        Yields:
            Nothing (Command).
        """
        from .abc.sequence_interactions import SetIndex

        return SetIndex(self, index, value)

    def __delitem__(self, index: IntArg) -> Any:  # noqa: ANN401
        """Subscript delete: del self[index].

        Args:
            index: the position to remove. An out-of-range index raises at
                evaluation time, matching Python.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain List value.

        Yields:
            Nothing (Command).
        """
        from .abc.sequence_interactions import DelIndex

        return DelIndex(self, index)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: ListArg[T]) -> Bool:
        """Self strictly greater than other, element-by-element.

        Args:
            other: the list to compare against.

        Yields:
            True when self sorts after other, False otherwise. INVALID when
            either operand is not a List or is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 3) > nu.List.of(1, 2))[0]
            True
        """
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: ListArg[T]) -> Bool:
        """Self strictly less than other, element-by-element.

        Args:
            other: the list to compare against.

        Yields:
            True when self sorts before other, False otherwise. INVALID
            when either operand is not a List or is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2) < nu.List.of(1, 3))[0]
            True
        """
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: ListArg[T]) -> Bool:
        """Self greater than or equal to other, element-by-element.

        Args:
            other: the list to compare against.

        Yields:
            True when self sorts after or equal to other, False otherwise.
            INVALID when either operand is not a List or is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2) >= nu.List.of(1, 2))[0]
            True
        """
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: ListArg[T]) -> Bool:
        """Self less than or equal to other, element-by-element.

        Args:
            other: the list to compare against.

        Yields:
            True when self sorts before or equal to other, False otherwise.
            INVALID when either operand is not a List or is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2) <= nu.List.of(1, 3))[0]
            True
        """
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: ListArg[T]) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the list to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the lists compare equal, False otherwise. INVALID
            when either operand is not a List or is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2) == nu.List.of(1, 2))[0]
            True
        """
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: ListArg[T]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the list to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the lists differ, False otherwise. INVALID when
            either operand is not a List or is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2) != nu.List.of(1, 3))[0]
            True
        """
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: ListArg[T]) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For value comparison
              use `==` instead. Two lists built separately with equal
              elements are not the same object.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.List.of(1, 2).is_(nu.List.of(1, 2)))[0]
            False
        """
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
