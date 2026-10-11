"""Grid Shape -- one child slot per cell. STUB over ``GridRef``; the grid unit fills it in."""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.containers.grid import GridRef


__all__ = ["Grid"]


class Grid(Section):
    """Equal cells, one per slot. Props as ``GridRef.slot``."""

    _ref_cls = GridRef
