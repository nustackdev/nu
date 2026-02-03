"""Span — grouping (context boundary).

Spans scope context for children and return the last child's result.
Concrete spans (Atomic, etc.) defined downstream.
"""

from __future__ import annotations

from .base import Span


__all__ = [
    "Span",
]
