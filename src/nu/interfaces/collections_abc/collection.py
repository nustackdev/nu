"""Collection capability - protocols + bases.

CollectionProtocol/Base = Sized + Iterable + Container.

Follows Python's collections.abc.Collection pattern.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
    ElementResultT: Wrapped result for element-level operations
"""

from __future__ import annotations

from typing import Protocol

from .container import ContainerBase, ContainerProtocol
from .iterable import IterableBase, IterableProtocol
from .sized import SizedBase, SizedProtocol


__all__ = [
    "CollectionBase",
    "CollectionProtocol",
]


# =============================================================================
# COLLECTION
# =============================================================================


class CollectionProtocol[ElementT, CollectionResultT, ElementResultT](
    SizedProtocol,
    IterableProtocol[ElementT, CollectionResultT, ElementResultT],
    ContainerProtocol,
    Protocol,
):
    """Protocol for collection values - like collections.abc.Collection.

    Combines Sized (len), Iterable (iteration support), and Container
    (containment checks).

    Type Parameters:
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops
        ElementResultT: Result for element-level ops
    """

    ...


class CollectionBase[ElementT, CollectionResultT, ElementResultT](
    SizedBase,
    IterableBase[ElementT, CollectionResultT, ElementResultT],
    ContainerBase,
):
    """Base for collection values - like collections.abc.Collection.

    Inherits len() from SizedBase, __contains__ from ContainerBase,
    and wrapping infrastructure from IterableBase.

    Type Parameters:
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops
        ElementResultT: Result for element-level ops
    """

    pass
