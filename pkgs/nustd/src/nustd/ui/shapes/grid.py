"""Grid Shape -- equal cells, declared.

A Section over ``GridRef``: ``_ref_cls`` names the Ref, the wire type and
the slot defaults come from it, and ``slot(**props)`` hands the props over
as they are. Each slot is one cell, in the order declared.

    class Stats(Grid):
        users = CardRef.slot(title="Users")
        jobs = CardRef.slot(title="Jobs")
        errors = CardRef.slot(title="Errors")

    stats = Stats.slot(columns=3, gap=3)
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.containers.grid import GridRef


__all__ = ["Grid"]


class Grid(Section):
    """Its slots in equal cells, row after row. Props as ``GridRef.slot``."""

    _ref_cls = GridRef
