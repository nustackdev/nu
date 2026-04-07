"""Collection capability.

CollectionI = Sized + Iterable + Container.

Follows Python's collections.abc.Collection pattern.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
    ElementResultT: Wrapped result for element-level operations
"""

from __future__ import annotations

from .container import ContainerI
from .iterable import IterableI
from .sized import SizedI


__all__ = [
    "CollectionI",
]


class CollectionI[ElementT, CollectionResultT, ElementResultT](
    SizedI,
    IterableI[ElementT, CollectionResultT, ElementResultT],
    ContainerI,
):
    """Base for collection values - like collections.abc.Collection.

    Inherits len() from SizedI, __contains__ from ContainerI,
    and wrapping infrastructure from IterableI.

    Type Parameters:
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops
        ElementResultT: Result for element-level ops
    """

    pass
