"""Shape system — declarative document structure definitions.

Shape: Base class for declarative shape definitions.
ShapeMeta: Metaclass that processes slot definitions at class creation time.
SlotDescriptor: Descriptor bridging slot definitions to refs at runtime.
Slot: Universal slot that creates any Ref type.
"""

from .shape import Shape, ShapeMeta, SlotDescriptor
from .slot import Slot


__all__ = [
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
]
