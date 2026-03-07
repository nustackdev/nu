"""Flow — ordering (when).

Flows define when children execute relative to each other.
Concrete flows (Seq, Par, Cond) defined downstream.
"""

from __future__ import annotations

from .base import Flow


__all__ = [
    "Flow",
]
