"""Collection abstractions — Sequence, Mapping, Set.

Composite collection types built on top of atomic capabilities.
"""

from .mapping import MappingBase, MappingProtocol, MutableMappingBase, MutableMappingProtocol
from .sequence import MutableSequenceBase, MutableSequenceProtocol, SequenceBase, SequenceProtocol
from .set_ import MutableSetBase, MutableSetProtocol, SetLikeBase, SetLikeProtocol


__all__ = [
    "MappingBase",
    "MappingProtocol",
    "MutableMappingBase",
    "MutableMappingProtocol",
    "MutableSequenceBase",
    "MutableSequenceProtocol",
    "MutableSetBase",
    "MutableSetProtocol",
    "SequenceBase",
    "SequenceProtocol",
    "SetLikeBase",
    "SetLikeProtocol",
]
