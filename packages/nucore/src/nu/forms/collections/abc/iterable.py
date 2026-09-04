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

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.lang import Form


if TYPE_CHECKING:
    from nu.forms.collections.iterator_ import Iterator
    from nu.lang import Nu


__all__ = [
    "IterableForm",
]


ElementT = TypeVar("ElementT")
CollectionResultT = TypeVar("CollectionResultT")
ElementResultT = TypeVar("ElementResultT")


class IterableForm(Form, Generic[ElementT, CollectionResultT, ElementResultT]):
    """Base for values that support iteration, like collections.abc.Iterable.

    Subclasses (SequenceForm, MappingForm, etc.) use the wrapping hooks here
    to wrap op results in their own collection and element types.
    Higher-order interactions (Map, Filter, Reduce, etc.) are standalone
    functions in `abc.fn`, not methods on this class.

    Notes:
        - Subclasses must override `_wrap_iterable_result` and
          `_wrap_element_result`.

    Example:
        iter(nu.List([1, 2, 3]))
    """

    def __iter__(self) -> Iterator[ElementT]:
        """Open self into a lazy iterator stream (Python's `iter`).

        Notes:
            - A pure read: builds the `Iter` stream query over self and
              wraps it as an Iterator.
            - Unlike `len`/`contains`, whose results Python coerces at the C
              level, `iter` keeps whatever `__iter__` returns, so the Nu
              tree survives.
            - The result is a lazy stream, consumed by a Flow rather than
              handed straight to `nu.run`.

        Yields:
            An Iterator streaming self's elements.

        Example:
            iter(nu.List([1, 2, 3]))
        """
        from nu.core import Iter
        from nu.forms.collections.iterator_ import Iterator

        return Iterator(Iter(self))

    def _wrap_iterable_result(self, operand: Nu) -> CollectionResultT:
        """Wrap operand in the subclass's collection type.

        Notes:
            - Abstract hook. Every concrete subclass must override this;
              the base raises.
        """
        raise NotImplementedError()

    def _wrap_element_result(self, operand: Nu) -> ElementResultT:
        """Wrap operand in the subclass's element type.

        Notes:
            - Abstract hook. Every concrete subclass must override this;
              the base raises.
        """
        raise NotImplementedError()
