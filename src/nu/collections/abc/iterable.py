"""Iterable capability.

IterableI: wrapping infrastructure for collection results.

Follows Python's collections.abc.Iterable pattern. In Nu's tree model,
iteration is controlled by Flows (ForEach, ForRange), not Python's
iterator protocol. This marks types as iterable and provides
the wrapping infrastructure for typed results.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
    ElementResultT: Wrapped result for element-level operations
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Interface


if TYPE_CHECKING:
    from nu.terms import Nu


__all__ = [
    "IterableI",
]


class IterableI[ElementT, CollectionResultT, ElementResultT](Interface):
    """Base for values that support iteration.

    Provides wrapping infrastructure used by subclass traits
    (SequenceI, MappingI, etc.) to wrap op results
    in appropriate Value types.

    Higher-order operations (Map, Filter, Reduce, etc.) are standalone
    functions in ``abc.fn``.

    Subclasses must override:
        _wrap_iterable_result(operand) -> CollectionResultT
            Wrap a op result in the appropriate collection type.
        _wrap_element_result(operand) -> ElementResultT
            Wrap a op result in the appropriate element type.

    Type Parameters:
        ElementT: Native Python element type (int, str, dict, etc.)
        CollectionResultT: Result type for ops that return collections
        ElementResultT: Result type for ops that extract single elements
    """

    def _wrap_iterable_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap result in appropriate collection type."""
        raise NotImplementedError()

    def _wrap_element_result(self, operand: Nu) -> ElementResultT:
        """Override in subclass to wrap result in appropriate element type."""
        raise NotImplementedError()
