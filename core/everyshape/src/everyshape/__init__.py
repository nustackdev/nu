"""everyshape - Declarative document model for everybase.

Provides the shape metaclass system for defining hierarchical
document structures with typed slots.

Key Classes:
    ShapeMeta: Metaclass that processes slot definitions at class creation time.
    ShapeBase: Base class for declarative shape definitions.
    SlotDescriptor: Descriptor bridging slot definitions to refs at runtime.
"""

from everyshape.shape import ShapeBase, ShapeMeta, SlotDescriptor


__all__ = [
    "ShapeBase",
    "ShapeMeta",
    "SlotDescriptor",
]
