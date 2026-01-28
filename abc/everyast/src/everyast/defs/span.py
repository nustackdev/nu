"""Span -- cohesion boundary (2-cell / region)."""

from __future__ import annotations

from abc import ABC

from .exec import Exec


__all__ = [
    "Span",
]


class Span(Exec, ABC):
    """Cohesion boundary (2-cell). Transparent.

    Spans declare shared properties among their children.
    They form the cohesion boundaries of the topology.

    Removing spans doesn't change computation (transparency).
    Downstream packages add absorption behavior
    (children's needs minus provided types).

    Concrete spans (Atomic, SpanContext, RootSpan, etc.)
    are defined downstream.

    Design rules:
        S2: Span transparency -- removing spans doesn't change computation.
        S4: Spans own exactly one concern -- cohesion (what's shared).
    """

    __slots__ = ()
