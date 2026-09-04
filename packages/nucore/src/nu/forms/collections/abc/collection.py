"""Collection capability.

CollectionForm = Sized + Iterable + Container.

Follows Python's collections.abc.Collection pattern.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level interactions
    ElementResultT: Wrapped result for element-level interactions
"""

from __future__ import annotations

from typing import Generic, TypeVar

from .container import ContainerForm
from .iterable import IterableForm
from .sized import SizedForm


__all__ = [
    "CollectionForm",
]


ElementT = TypeVar("ElementT")
CollectionResultT = TypeVar("CollectionResultT")
ElementResultT = TypeVar("ElementResultT")


class CollectionForm(
    SizedForm,
    IterableForm[ElementT, CollectionResultT, ElementResultT],
    ContainerForm,
    Generic[ElementT, CollectionResultT, ElementResultT],
):
    """Base for collection values, like collections.abc.Collection.

    Combines `len()` from SizedForm, `contains()` from ContainerForm, and
    the result-wrapping infrastructure from IterableForm.

    Example:
        >>> nu.run(nu.List([1, 2, 3]).len())[0]
        3
    """

    def extract(self) -> object:
        """Materialise the full subtree rooted at self.

        Notes:
            - Recursively pulls the whole subtree out of the fabric into a
              plain Python value (dict / list / nested mix), unlike a plain
              read which only yields the value at self's own address.
            - Needs self bound in a live fabric; it isn't a scalar
              expression `nu.run` can evaluate on its own.

        Yields:
            The materialised Python value. Preserves EMPTY vs INVALID when
            self is a sentinel rather than collapsing them together.

        Example:
            nu.List([1, 2, 3]).extract()
        """
        from nu.domains.shape.interactions import Extract

        return Extract(self)
