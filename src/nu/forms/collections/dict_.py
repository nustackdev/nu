"""DictForm - dict interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.lang import TypedNu

from .abc import MutableMappingForm
from .abc.mapping_interactions import DictCreate, DictOf


if TYPE_CHECKING:
    from nu.lang import Arg, DictArg, Nu

    from ..primitives import (
        AnyForm,
        BoolForm,
        BytesForm,
        FloatForm,
        IntForm,
        StrForm,
    )
    from .list_ import ListForm
    from .views import DictItemsForm, DictKeysForm, DictValuesForm


__all__ = [
    "DictForm",
]


class DictForm[K, V](
    MutableMappingForm[dict[K, V], K, V, "DictForm[K, V]", "AnyForm"],
    TypedNu[dict[K, V]],
):
    """Dict interface. Mutable mapping + comparable."""

    @classmethod
    def create(cls) -> DictForm[K, V]:
        """Yield a fresh empty dict."""
        return cls(DictCreate())

    @classmethod
    def of(cls, **fields: Arg) -> DictForm[str, V]:
        """Yield a dict from named field expressions.

        ``DictForm.of(a=x, b=y)`` evaluates each value in the current context
        and zips the names back in: ``{"a": <x>, "b": <y>}``. Values may be Nu
        expressions or plain literals. A field that resolves to a sentinel
        collapses the whole result to Invalid.
        """
        return cls(DictOf(**fields))

    def _wrap_keys_result(self, operand: Nu) -> DictKeysForm:
        """Wrap operand as DictKeysForm."""
        from .views import DictKeysForm

        return DictKeysForm(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesForm:
        """Wrap operand as DictValuesForm."""
        from .views import DictValuesForm

        return DictValuesForm(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsForm:
        """Wrap operand as DictItemsForm."""
        from .views import DictItemsForm

        return DictItemsForm(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as a value-typed Form when known; AnyForm otherwise.

        When the wrapping Form carries an annotation-derived ``TypeInfo`` on
        its payload (a Ref like ``PrimitiveDictRef[str, int]``), dispatch the
        value elem to its concrete Form (``IntForm`` here). Plain value-node
        ``DictForm`` s (no payload) fall back to ``AnyForm`` - the honest
        terminal for value-Form descent without narrowing context.
        """
        ti = self._payload.get("type_info")
        if ti is not None and ti.elem is not None:
            form_cls = ti.elem.to_form()
            return form_cls(operand)  # type: ignore[return-value]
        from ..primitives import AnyForm

        return AnyForm(operand)

    # ---- static overloads: narrow value type on subscript ---------------
    #
    # Runtime dispatch above; here we tell mypy which concrete Form to
    # expect based on ``V``. Applies to any subclass (PrimitiveDictRef[K, V],
    # nudle refs holding dicts, etc.) that specializes ``V``.

    @overload
    def __getitem__(self: DictForm[K, bool], key: Arg[K]) -> BoolForm: ...
    @overload
    def __getitem__(self: DictForm[K, int], key: Arg[K]) -> IntForm: ...
    @overload
    def __getitem__(self: DictForm[K, float], key: Arg[K]) -> FloatForm: ...
    @overload
    def __getitem__(self: DictForm[K, str], key: Arg[K]) -> StrForm: ...
    @overload
    def __getitem__(self: DictForm[K, bytes], key: Arg[K]) -> BytesForm: ...
    @overload
    def __getitem__(self, key: Arg[K]) -> AnyForm: ...
    def __getitem__(self, key):  # type: ignore[no-untyped-def]
        return super().__getitem__(key)

    def _wrap_mapping_result(self, operand: Nu) -> DictForm[K, V]:
        """Wrap operand as DictForm."""
        return DictForm(operand)

    def keys(self) -> DictKeysForm[K]:  # type: ignore[override]
        """Get all keys as a DictKeysForm."""
        from .abc.mapping_interactions import KeysQuery

        return self._wrap_keys_result(KeysQuery(self))

    def values(self) -> DictValuesForm[V]:  # type: ignore[override]
        """Get all values as a DictValuesForm."""
        from .abc.mapping_interactions import ValuesQuery

        return self._wrap_values_result(ValuesQuery(self))

    def items(self) -> DictItemsForm[K, V]:  # type: ignore[override]
        """Get all key-value pairs as a DictItemsForm."""
        from .abc.mapping_interactions import ItemsQuery

        return self._wrap_items_result(ItemsQuery(self))

    def _wrap_iterable_result(self, operand: Nu) -> ListForm:
        """Wrap operand as ListForm."""
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as AnyForm element."""
        from ..primitives import AnyForm

        return AnyForm(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DictArg[K, V]) -> BoolForm:
        from nu.core import GtQuery

        from ..primitives import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: DictArg[K, V]) -> BoolForm:
        from nu.core import LtQuery

        from ..primitives import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: DictArg[K, V]) -> BoolForm:
        from nu.core import GeQuery

        from ..primitives import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: DictArg[K, V]) -> BoolForm:
        from nu.core import LeQuery

        from ..primitives import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: DictArg[K, V]) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from ..primitives import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: DictArg[K, V]) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from ..primitives import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: DictArg[K, V]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from ..primitives import BoolForm

        return BoolForm(IsQuery(self, other))
