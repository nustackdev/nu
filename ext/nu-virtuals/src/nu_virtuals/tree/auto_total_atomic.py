"""auto_total_atomic — wrap each virtuals-touching Flow as one whole boundary.

Totalistic strategy: a Flow is treated as one atomic unit; the entire
Flow gets a single Atomic boundary. Inner Flows of an already-wrapped
Flow are not re-wrapped.

Use when you want one transaction per Flow regardless of branching
shape. For per-branch granularity (each child of a Flow gets its own
Bracket — natural for Parallel and concurrent branches), use
``auto_flow_atomic``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.shapes.tree.wrap import touches_fabric, wrap_flows

from ..refs.base import PrimitiveRef, ViewRef
from ..refs.flat import FlatRef
from ..spans.atomic import Atomic


if TYPE_CHECKING:
    from collections.abc import Hashable

    from nu.terms import Nu


__all__ = [
    "auto_total_atomic",
]


_VIRTUALS_REFS = (ViewRef, PrimitiveRef, FlatRef)


def auto_total_atomic(tree: Nu, *, scope: Hashable | None = None) -> Nu:
    """Wrap each outermost virtuals-touching Flow with one Atomic.

    Atomic resolves to Snapshot (read-only Flow) or Transaction (Flow
    with any WRITE) based on tracked effects.

    Args:
        tree: Nu tree root.
        scope: Optional shape root tag for the boundary's navigator binding.
    """
    return wrap_flows(
        tree,
        wrapper=lambda flow: Atomic(flow, scope=scope),
        predicate=lambda flow: touches_fabric(flow, _VIRTUALS_REFS),
    )
