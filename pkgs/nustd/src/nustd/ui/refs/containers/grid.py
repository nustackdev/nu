"""``GridRef`` -- children in equal cells, row after row.

STUB, wired end to end so the grid unit only fills it in: the class, its
wire type, a first ``slot()`` and the Shape over it exist, the kit node draws
its children in a plain grid. The column and gap rules are the grid unit's.
"""

from __future__ import annotations

from typing_extensions import Self

from .base import ContainerRef


__all__ = ["GridRef"]


class GridRef(ContainerRef):
    """Equal cells, one child per cell. ``columns=0`` lets the width decide."""

    _wire_type = "Grid"

    @classmethod
    def slot(cls, *, columns: int = 0, gap: int = 4) -> Self:
        return super().slot(columns=int(columns), gap=int(gap))
