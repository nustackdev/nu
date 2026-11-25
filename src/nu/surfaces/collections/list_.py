"""List - list interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

from .abc import MutableSequenceSurface


if TYPE_CHECKING:
    from nu.forms import Bool, Bytes, Float, Int, List, Object, Str
    from nu.lang import IntArg, ListArg, Nu


__all__ = [
    "ListSurface",
]


T = TypeVar("T")


class ListSurface(MutableSequenceSurface[list[T], T, "List[T]", "Object"], Generic[T]):
    """The methods of ``List``, shared by the ``List`` form and every ref that holds one."""

    def _wrap_sliceable_result(self, operand: Nu) -> List:
        """Wrap operand as List for slice results."""
        from nu.forms import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Object:
        """Wrap operand as an elem-typed Form when known; Object otherwise.

        Notes:
            - When the wrapping Form carries an annotation-derived
              `TypeInfo` in its `type_info` field (i.e. it's a Ref like
              `PrimitiveListRef[str]`), dispatch the elem to its concrete
              Form (`Str` here).
            - Plain value-node `List`s (no type info) fall back to `Object` -
              the honest terminal for value-Form descent without
              narrowing context.
        """
        ti = self._type_info
        if ti is not None and ti.elem is not None:
            form_cls = ti.elem.to_form()
            return form_cls(operand)  # type: ignore[return-value]
        from nu.forms import Object

        return Object(operand)

    # ---- static overloads: narrow elem type on subscript ----------------
    #
    # Runtime dispatch above; here we tell mypy which concrete Form to
    # expect based on ``T``. Applies to any subclass (PrimitiveListRef[T],
    # nudle refs holding lists, etc.) that specializes ``T``.

    @overload
    def __getitem__(self: ListSurface[bool], key: IntArg) -> Bool: ...
    @overload
    def __getitem__(self: ListSurface[int], key: IntArg) -> Int: ...
    @overload
    def __getitem__(self: ListSurface[float], key: IntArg) -> Float: ...
    @overload
    def __getitem__(self: ListSurface[str], key: IntArg) -> Str: ...
    @overload
    def __getitem__(self: ListSurface[bytes], key: IntArg) -> Bytes: ...
    @overload
    def __getitem__(self, key: IntArg) -> Object: ...
    @overload
    def __getitem__(self, key: slice) -> List[T]: ...
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
              else falls back to `Object`.

        Yields:
            The element for an int key, the sublist for a slice.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3)[1])[0]
            2

            >>> nu.run(nu.List.of(1, 2, 3)[1:3])[0]
            [2, 3]
        """
        return super().__getitem__(key)

    # =========================================================================
    # LIST-ONLY (not on collections.abc.MutableSequence)
    # =========================================================================

    def sort(self) -> Any:  # noqa: ANN401
        """Sort self in place, ascending, using the elements' natural order.

        Notes:
            - No `key` support yet; sorting by a derived key is deferred.
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain List value.

        Yields:
            Nothing (Command).
        """
        from .abc.sequence_interactions import Sort

        return Sort(self)

    def copy(self) -> List[T]:
        """Shallow copy of self: a new list with the same elements.

        Notes:
            - A Query, not a mutator: it doesn't mutate self and evaluates
              fine against a plain list value.

        Yields:
            The copy.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).copy())[0]
            [1, 2, 3]
        """
        from .abc.sequence_interactions import Copy

        return self._wrap_sliceable_result(Copy(self))

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: ListArg[T]) -> List[T]:
        """Concatenation of self and other.

        Args:
            other: the list to append to self.

        Yields:
            The concatenation.

        Example:
            >>> nu.run(nu.List.of(1, 2) + nu.List.of(3, 4))[0]
            [1, 2, 3, 4]
        """
        from nu.core import Add
        from nu.forms import List

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
            The concatenation.

        Example:
            >>> nu.run([1, 2] + nu.List.of(3, 4))[0]
            [1, 2, 3, 4]
        """
        from nu.core import Add
        from nu.forms import List

        return List(Add(other, self))

    def __mul__(self, n: IntArg) -> List[T]:
        """Self repeated n times.

        Args:
            n: the repeat count. `0` or negative yields an empty list.

        Yields:
            The repeated list.

        Example:
            >>> nu.run(nu.List.of(1, 2) * 3)[0]
            [1, 2, 1, 2, 1, 2]
        """
        from nu.core import Mul
        from nu.forms import List

        return List(Mul(self, n))

    def __rmul__(self, n: IntArg) -> List[T]:
        """Self repeated n times, with self on the right of the `*`.

        Args:
            n: the repeat count, on the left of the `*`.

        Notes:
            - Reached only when the left operand is a plain Python int. A
              Nu Int on the left goes through `__mul__` instead.

        Yields:
            The repeated list.

        Example:
            >>> nu.run(3 * nu.List.of(1, 2))[0]
            [1, 2, 1, 2, 1, 2]
        """
        from nu.core import Mul
        from nu.forms import List

        return List(Mul(n, self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: ListArg[T]) -> Bool:
        """Self strictly greater than other, element-by-element.

        Args:
            other: the list to compare against.

        Yields:
            True when self sorts after other, False otherwise.

        Example:
            >>> nu.run(nu.List.of(1, 3) > nu.List.of(1, 2))[0]
            True
        """
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: ListArg[T]) -> Bool:
        """Self strictly less than other, element-by-element.

        Args:
            other: the list to compare against.

        Yields:
            True when self sorts before other, False otherwise.

        Example:
            >>> nu.run(nu.List.of(1, 2) < nu.List.of(1, 3))[0]
            True
        """
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: ListArg[T]) -> Bool:
        """Self greater than or equal to other, element-by-element.

        Args:
            other: the list to compare against.

        Yields:
            True when self sorts after or equal to other, False otherwise.

        Example:
            >>> nu.run(nu.List.of(1, 2) >= nu.List.of(1, 2))[0]
            True
        """
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: ListArg[T]) -> Bool:
        """Self less than or equal to other, element-by-element.

        Args:
            other: the list to compare against.

        Yields:
            True when self sorts before or equal to other, False otherwise.

        Example:
            >>> nu.run(nu.List.of(1, 2) <= nu.List.of(1, 3))[0]
            True
        """
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def __eq__(self, other: ListArg[T]) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the list to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the lists compare equal, False otherwise.

        Example:
            >>> nu.run(nu.List.of(1, 2) == nu.List.of(1, 2))[0]
            True
        """
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: ListArg[T]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the list to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the lists differ, False otherwise.

        Example:
            >>> nu.run(nu.List.of(1, 2) != nu.List.of(1, 3))[0]
            True
        """
        from nu.core import Ne
        from nu.forms import Bool

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
        from nu.forms import Bool

        return Bool(Is(self, other))
