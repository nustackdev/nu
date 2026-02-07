"""Model -- abstract base for declarative structure definitions."""

from __future__ import annotations


__all__ = [
    "Model",
]


class Model:
    """Abstract base for declarative structure definitions.

    Model is the substrate-agnostic base class. Model packages
    extend it with their own field machinery:

    - Shape (everyshape): document model with slots for hierarchical KV structures
    - Table (everytable): relational model (future)

    Models define *what exists and where it lives*.
    They are purely structural -- no behavior or validation logic.
    """
