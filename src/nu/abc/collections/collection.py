"""Collection capability — protocols + bases.

CollectionProtocol/Base = Iterable (wrapping infrastructure only)

Follows Python's collections.abc.Collection pattern.
Len and Contains are standalone functions in ``abc.fn``.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
    ElementResultT: Wrapped result for element-level operations
"""

from __future__ import annotations

from typing import Protocol

from .iterable import IterableBase, IterableProtocol


__all__ = [
    "CollectionBase",
    "CollectionProtocol",
]


# =============================================================================
# COLLECTION
# =============================================================================


class CollectionProtocol[ElementT, CollectionResultT, ElementResultT](
    IterableProtocol[ElementT, CollectionResultT, ElementResultT],
    Protocol,
):
    """Protocol for collection values — like collections.abc.Collection.

    Type Parameters:
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops
        ElementResultT: Result for element-level ops
    """

    ...


class CollectionBase[ElementT, CollectionResultT, ElementResultT](
    IterableBase[ElementT, CollectionResultT, ElementResultT],
):
    """Base for collection values — like collections.abc.Collection.

    Type Parameters:
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops
        ElementResultT: Result for element-level ops
    """

    pass
