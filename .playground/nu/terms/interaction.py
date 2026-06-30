"""Interaction - the work-kind base.

Top-level kind alongside Ref. The four sub-kinds Query, Command, Flow,
Span all inherit from this. Interaction itself is abstract; concrete
work always goes through one of the sub-kinds.

Interaction sits between NuBase and the sub-kind bases purely as a
classification anchor: `isinstance(x, Interaction)` is the right check
when the question is "is this a work atom (vs. a Ref)?"
"""

from __future__ import annotations

from .nu import NuBase


__all__ = [
    "Interaction",
]


class Interaction(NuBase):
    """Abstract Interaction base. Sub-kinds: Query, Command, Flow, Span."""
