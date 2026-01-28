"""Span — cohesion boundary (2-cell).

Spans declare shared properties among children.
Concrete spans (Atomic, etc.) defined downstream.
"""

from __future__ import annotations

from .base import Span


__all__ = [
    "Span",
]
