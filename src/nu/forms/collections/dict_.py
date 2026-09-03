"""Dict - dict interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, overload

from nu.lang import TypedNu

from .abc import MutableMappingForm
from .abc.mapping_interactions import DictCreate, DictOf


if TYPE_CHECKING:
    from nu.lang import Arg, DictArg, Nu

    from ..primitives import (
        Any,
        Bool,
        Bytes,
        Float,
        Int,
        Str,
    )
    from .list_ import List
    from .views import DictItems, DictKeys, DictValues


__all__ = [
    "Dict",
]


K = TypeVar("K")
V = TypeVar("V")


class Dict(
    MutableMappingForm[dict[K, V], K, V, "Dict[K, V]", "Any"],
    TypedNu[dict[K, V]],
    Generic[K, V],
):
    """Dict interface. Mutable mapping + comparable.

    Notes:
        - Keys preserve insertion order, matching Python's `dict`.
        - Ordering comparisons (`>`, `<`, `>=`, `<=`) raise `TypeError` at
          evaluation time rather than yielding INVALID - Python dicts don't
          support them either. Use `==`/`!=` for content comparison.
        - `is_` tests object identity. Each evaluation of a `Dict.of`/
          `Dict.create` expression builds a fresh dict, so comparing two
          separately-built dicts with `is_` is False even when their
          contents match, unlike Python's small-string interning for Str.

    Example:
        >>> nu.run(nu.Dict.of(a=1, b=2))[0]
        {'a': 1, 'b': 2}
    """

    @classmethod
    def create(cls) -> Dict[K, V]:
        """Fresh empty dict.

        Yields:
            A new, empty dict. Never a sentinel.

        Example:
            >>> nu.run(nu.Dict.create())[0]
            {}
        """
        return cls(DictCreate())

    @classmethod
    def of(cls, **fields: Arg) -> Dict[str, V]:
        """Dict built from named field expressions.

        Args:
            fields: keyword arguments, each evaluated in the current
                context and zipped back in by name: `a=x, b=y` builds
                `{"a": <x>, "b": <y>}`. Values may be Nu expressions or
                plain literals.

        Notes:
            - A field that resolves to a sentinel collapses the whole
              result to INVALID.

        Yields:
            The assembled dict. INVALID when any field is a sentinel.

        Example:
            >>> nu.run(nu.Dict.of(a=1, b=2))[0]
            {'a': 1, 'b': 2}
        """
        return cls(DictOf(**fields))

    def _wrap_keys_result(self, operand: Nu) -> DictKeys:
        """Wrap operand as DictKeys."""
        from .views import DictKeys

        return DictKeys(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValues:
        """Wrap operand as DictValues."""
        from .views import DictValues

        return DictValues(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItems:
        """Wrap operand as DictItems."""
        from .views import DictItems

        return DictItems(operand)

    def _wrap_value_result(self, operand: Nu) -> Any:
        """Wrap operand as a value-typed Form when known; Any otherwise.

        When the wrapping Form carries an annotation-derived ``TypeInfo`` on
        its payload (a Ref like ``PrimitiveDictRef[str, int]``), dispatch the
        value elem to its concrete Form (``Int`` here). Plain value-node
        ``Dict`` s (no payload) fall back to ``Any`` - the honest
        terminal for value-Form descent without narrowing context.
        """
        ti = self._payload.get("type_info")
        if ti is not None and ti.elem is not None:
            form_cls = ti.elem.to_form()
            return form_cls(operand)  # type: ignore[return-value]
        from ..primitives import Any

        return Any(operand)

    # ---- static overloads: narrow value type on subscript ---------------
    #
    # Runtime dispatch above; here we tell mypy which concrete Form to
    # expect based on ``V``. Applies to any subclass (PrimitiveDictRef[K, V],
    # nudle refs holding dicts, etc.) that specializes ``V``.

    @overload
    def __getitem__(self: Dict[K, bool], key: Arg[K]) -> Bool: ...
    @overload
    def __getitem__(self: Dict[K, int], key: Arg[K]) -> Int: ...
    @overload
    def __getitem__(self: Dict[K, float], key: Arg[K]) -> Float: ...
    @overload
    def __getitem__(self: Dict[K, str], key: Arg[K]) -> Str: ...
    @overload
    def __getitem__(self: Dict[K, bytes], key: Arg[K]) -> Bytes: ...
    @overload
    def __getitem__(self, key: Arg[K]) -> Any: ...
    def __getitem__(self, key):  # type: ignore[no-untyped-def]
        """Value at key.

        Args:
            key: the key to look up.

        Notes:
            - A missing key raises `KeyError` at evaluation time, matching
              Python's `dict[key]`. Use `get_item` for a default instead.

        Yields:
            The value, narrowed to a concrete Form (Bool, Int, Float, Str,
            Bytes) when `V` is a known primitive type, Any otherwise.
            INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Dict.of(a=1, b=2)["a"])[0]
            1
        """
        return super().__getitem__(key)

    def _wrap_mapping_result(self, operand: Nu) -> Dict[K, V]:
        """Wrap operand as Dict."""
        return Dict(operand)

    def keys(self) -> DictKeys[K]:  # type: ignore[override]
        """Self's keys as a live view.

        Notes:
            - Insertion order, matching Python's `dict.keys()`.

        Yields:
            The keys, wrapped as DictKeys. INVALID when self is a sentinel.

        Example:
            >>> list(nu.run(nu.Dict.of(a=1, b=2).keys())[0])
            ['a', 'b']
        """
        from .abc.mapping_interactions import Keys

        return self._wrap_keys_result(Keys(self))

    def values(self) -> DictValues[V]:  # type: ignore[override]
        """Self's values as a live view.

        Notes:
            - Insertion order, matching Python's `dict.values()`.

        Yields:
            The values, wrapped as DictValues. INVALID when self is a
            sentinel.

        Example:
            >>> list(nu.run(nu.Dict.of(a=1, b=2).values())[0])
            [1, 2]
        """
        from .abc.mapping_interactions import Values

        return self._wrap_values_result(Values(self))

    def items(self) -> DictItems[K, V]:  # type: ignore[override]
        """Self's key-value pairs as a live view.

        Notes:
            - Insertion order, matching Python's `dict.items()`.

        Yields:
            The (key, value) pairs, wrapped as DictItems. INVALID when self
            is a sentinel.

        Example:
            >>> list(nu.run(nu.Dict.of(a=1, b=2).items())[0])
            [('a', 1), ('b', 2)]
        """
        from .abc.mapping_interactions import Items

        return self._wrap_items_result(Items(self))

    def _wrap_iterable_result(self, operand: Nu) -> List:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element."""
        from ..primitives import Any

        return Any(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DictArg[K, V]) -> Bool:
        """Self strictly greater than other.

        Args:
            other: the dict to compare against.

        Notes:
            - Python dicts don't support ordering, so this raises
              `TypeError` at evaluation time rather than yielding INVALID.
              Compare with `==`/`!=` instead.

        Yields:
            Never yields; the comparison always raises.

        Example:
            >>> nu.run(nu.Dict.of(a=1) > nu.Dict.of(a=2))[0]
            Traceback (most recent call last):
                ...
            TypeError: '>' not supported between instances of 'dict' and 'dict'
        """
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: DictArg[K, V]) -> Bool:
        """Self strictly less than other.

        Args:
            other: the dict to compare against.

        Notes:
            - Python dicts don't support ordering, so this raises
              `TypeError` at evaluation time rather than yielding INVALID.
              Compare with `==`/`!=` instead.

        Yields:
            Never yields; the comparison always raises.

        Example:
            >>> nu.run(nu.Dict.of(a=1) < nu.Dict.of(a=2))[0]
            Traceback (most recent call last):
                ...
            TypeError: '<' not supported between instances of 'dict' and 'dict'
        """
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: DictArg[K, V]) -> Bool:
        """Self greater than or equal to other.

        Args:
            other: the dict to compare against.

        Notes:
            - Python dicts don't support ordering, so this raises
              `TypeError` at evaluation time rather than yielding INVALID.
              Compare with `==`/`!=` instead.

        Yields:
            Never yields; the comparison always raises.

        Example:
            >>> nu.run(nu.Dict.of(a=1) >= nu.Dict.of(a=2))[0]
            Traceback (most recent call last):
                ...
            TypeError: '>=' not supported between instances of 'dict' and 'dict'
        """
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: DictArg[K, V]) -> Bool:
        """Self less than or equal to other.

        Args:
            other: the dict to compare against.

        Notes:
            - Python dicts don't support ordering, so this raises
              `TypeError` at evaluation time rather than yielding INVALID.
              Compare with `==`/`!=` instead.

        Yields:
            Never yields; the comparison always raises.

        Example:
            >>> nu.run(nu.Dict.of(a=1) <= nu.Dict.of(a=2))[0]
            Traceback (most recent call last):
                ...
            TypeError: '<=' not supported between instances of 'dict' and 'dict'
        """
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: DictArg[K, V]) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the dict to compare against.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the dicts have the same keys and values, False
            otherwise. INVALID when either operand is not a Dict or is a
            sentinel.

        Example:
            >>> nu.run(nu.Dict.of(a=1) == nu.Dict.of(a=1))[0]
            True
        """
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: DictArg[K, V]) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the dict to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the dicts differ, False otherwise. INVALID when
            either operand is not a Dict or is a sentinel.

        Example:
            >>> nu.run(nu.Dict.of(a=1) != nu.Dict.of(a=2))[0]
            True
        """
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: DictArg[K, V]) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For content comparison
              use `==` instead.
            - Each `Dict.of`/`Dict.create` expression builds a fresh dict on
              evaluation, so two separately-built dicts test not identical
              even with equal contents - there's no interning like Str gets
              for short literals.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.Dict.of(a=1).is_(nu.Dict.of(a=1)))[0]
            False
        """
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
