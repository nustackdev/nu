"""Shape system -- abstract bases for declarative structure definitions.

Shape:
    Abstract base for all shapes. Substrate packages extend this.

Slot:
    Abstract slot -- field definition that creates Refs.
"""

from __future__ import annotations

from .shape import Shape
from .slot import Slot


__all__ = [
    "Shape",
    "Slot",
]
