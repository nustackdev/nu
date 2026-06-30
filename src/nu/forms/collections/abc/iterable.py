"""Iterable capability.

IterableForm: wrapping infrastructure for collection results.

Follows Python's collections.abc.Iterable pattern. In Nu's tree model,
iteration is controlled by Flows (ForEachDo, ForRangeDo), not Python's
iterator protocol. This marks types as iterable and provides
the wrapping infrastructure for typed results.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level interactions
    ElementResultT: Wrapped result for element-level interactions
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.forms.collections.iterator_ import IteratorForm
    from nu.lang import Nu


__all__ = [
    "IterableForm",
]


class IterableForm[ElementT, CollectionResultT, ElementResultT](Form):
    """Base for values that support iteration.

    Provides wrapping infrastructure used by subclass traits
    (SequenceForm, MappingForm, etc.) to wrap op results
    in appropriate Value types.

    Higher-order interactions (MapQuery, FilterQuery, Reduce, etc.) are standalone
    functions in ``abc.fn``.

    Subclasses must override:
        _wrap_iterable_result(operand) -> CollectionResultT
            Wrap a op result in the appropriate collection type.
        _wrap_element_result(operand) -> ElementResultT
            Wrap a op result in the appropriate element type.

    Type Parameters:
        ElementT: Native Python element type (int, str, dict, etc.)
        CollectionResultT: Result type for interactions that return collections
        ElementResultT: Result type for interactions that extract single elements
    """

    def __iter__(self) -> IteratorForm[ElementT]:
        """Open this iterable into a lazy iterator stream (Python's ``iter``).

        A pure read: builds the StreamQuery ``IterQuery`` over this value and wraps
        it as an ``IteratorForm``. Unlike ``len``/``contains`` (whose results
        Python coerces at the C level), ``iter`` keeps whatever ``__iter__``
        returns, so the Nu tree survives.
        """
        from nu.core import IterQuery
        from nu.forms.collections.iterator_ import IteratorForm

        return IteratorForm(IterQuery(self))

    def _wrap_iterable_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap result in appropriate collection type."""
        raise NotImplementedError()

    def _wrap_element_result(self, operand: Nu) -> ElementResultT:
        """Override in subclass to wrap result in appropriate element type."""
        raise NotImplementedError()
