"""Collection + Clearable capabilities — protocols + bases.

CollectionProtocol/Base = Containable + Lengthable + Iterable
ClearableProtocol/Base = clear()

Follows Python's collections.abc.Collection pattern.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
    ElementResultT: Wrapped result for element-level operations
"""

from __future__ import annotations

from typing import Protocol

from ..capabilities.collection import (
    ContainableBase,
    ContainableProtocol,
    LengthableBase,
    LengthableProtocol,
)
from .iterable import IterableBase, IterableProtocol


__all__ = [
    "CollectionBase",
    "CollectionProtocol",
]


# =============================================================================
# COLLECTION
# =============================================================================


class CollectionProtocol[ElementT, CollectionResultT, ElementResultT](
    ContainableProtocol[ElementT],
    LengthableProtocol,
    IterableProtocol[ElementT, CollectionResultT, ElementResultT],
    Protocol,
):
    """Protocol for collection values — like collections.abc.Collection.

    Type Parameters:
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (map_, filter_)
        ElementResultT: Result for element-level ops (sum_, min_, max_)
    """

    ...


class CollectionBase[ElementT, CollectionResultT, ElementResultT](
    ContainableBase[ElementT],
    LengthableBase,
    IterableBase[ElementT, CollectionResultT, ElementResultT],
):
    """Base for collection values — like collections.abc.Collection.

    Type Parameters:
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (map_, filter_)
        ElementResultT: Result for element-level ops (sum_, min_, max_)
    """

    pass
