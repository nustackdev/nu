"""Shape -- abstract base for declarative structure definitions."""

from __future__ import annotations


__all__ = [
    "Shape",
]


class Shape:
    """Abstract base for declarative structure definitions.

    Shape is a substrate-agnostic base class. Substrate packages
    extend it with their own field machinery:

    - PVShape (every_pv): metaclass-based slots for PV storage

    Shapes define *what exists and where it lives*.
    They are purely structural -- no behavior or validation logic.
    """
