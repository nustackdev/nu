"""Collection capability.

CollectionSurface = Sized + Iterable + Container.

Follows Python's collections.abc.Collection pattern.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level interactions
    ElementResultT: Wrapped result for element-level interactions
"""

from __future__ import annotations

from typing import Generic, TypeVar

from .container import ContainerSurface
from .iterable import IterableSurface
from .sized import SizedSurface


__all__ = [
    "CollectionSurface",
]


ElementT = TypeVar("ElementT")
CollectionResultT = TypeVar("CollectionResultT")
ElementResultT = TypeVar("ElementResultT")


class CollectionSurface(
    SizedSurface,
    IterableSurface[ElementT, CollectionResultT, ElementResultT],
    ContainerSurface,
    Generic[ElementT, CollectionResultT, ElementResultT],
):
    """Base for collection values, like collections.abc.Collection.

    Combines `len()` from SizedSurface, `contains()` from ContainerSurface, and
    the result-wrapping infrastructure from IterableSurface.

    Example:
        >>> nu.run(nu.List([1, 2, 3]).len())[0]
        3
    """

    def extract(self) -> object:
        """Materialise the full subtree rooted at self.

        Notes:
            - Pulls the whole subtree out into a plain Python value (dict /
              list / nested mix), unlike a plain read, which may hand out a
              fabric's live handle.
            - A read that is an `nu.shape.Extractable` (a handle its fabric
              registered) is asked for its `extract()`; any other read is
              already plain and comes back as it is.

        Yields:
            The materialised Python value.

        Example:
            >>> nu.run(nu.List([1, 2, 3]).extract())[0]
            [1, 2, 3]
        """
        from nu.domains.shape.interactions import Extract

        return Extract(self)
