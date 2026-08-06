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
    """Dict interface. Mutable mapping + comparable."""

    @classmethod
    def create(cls) -> Dict[K, V]:
        """Yield a fresh empty dict."""
        return cls(DictCreate())

    @classmethod
    def of(cls, **fields: Arg) -> Dict[str, V]:
        """Yield a dict from named field expressions.

        ``Dict.of(a=x, b=y)`` evaluates each value in the current context
        and zips the names back in: ``{"a": <x>, "b": <y>}``. Values may be Nu
        expressions or plain literals. A field that resolves to a sentinel
        collapses the whole result to Invalid.
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
        return super().__getitem__(key)

    def _wrap_mapping_result(self, operand: Nu) -> Dict[K, V]:
        """Wrap operand as Dict."""
        return Dict(operand)

    def keys(self) -> DictKeys[K]:  # type: ignore[override]
        """Get all keys as a DictKeys."""
        from .abc.mapping_interactions import Keys

        return self._wrap_keys_result(Keys(self))

    def values(self) -> DictValues[V]:  # type: ignore[override]
        """Get all values as a DictValues."""
        from .abc.mapping_interactions import Values

        return self._wrap_values_result(Values(self))

    def items(self) -> DictItems[K, V]:  # type: ignore[override]
        """Get all key-value pairs as a DictItems."""
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
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: DictArg[K, V]) -> Bool:
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: DictArg[K, V]) -> Bool:
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: DictArg[K, V]) -> Bool:
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: DictArg[K, V]) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: DictArg[K, V]) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: DictArg[K, V]) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
