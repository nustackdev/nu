"""Collection abstractions — Sequence, Mapping, Set.

Composite collection types built on top of atomic capabilities.
"""

from .collection import (
    CollectionBase,
    CollectionProtocol,
)
from .iterable import (
    IterableBase,
    IterableProtocol,
)
from .mapping import MappingBase, MappingProtocol, MutableMappingBase, MutableMappingProtocol
from .sequence import MutableSequenceBase, MutableSequenceProtocol, SequenceBase, SequenceProtocol
from .set_ import MutableSetBase, MutableSetProtocol, SetLikeBase, SetLikeProtocol


__all__ = [  # noqa: RUF022
    # =========================================================================
    # ITERABLE
    # =========================================================================
    "IterableBase",
    "IterableProtocol",
    # =========================================================================
    # COLLECTION
    # =========================================================================
    "CollectionBase",
    "CollectionProtocol",
    # =========================================================================
    # SEQUENCE (+ Mutable)
    # =========================================================================
    "SequenceBase",
    "SequenceProtocol",
    "MutableSequenceBase",
    "MutableSequenceProtocol",
    # =========================================================================
    # MAPPING (+ Mutable)
    # =========================================================================
    "MappingBase",
    "MappingProtocol",
    "MutableMappingBase",
    "MutableMappingProtocol",
    # =========================================================================
    # SET (+ Mutable)
    # =========================================================================
    "SetLikeBase",
    "SetLikeProtocol",
    "MutableSetBase",
    "MutableSetProtocol",
]
