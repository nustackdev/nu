"""LineChart: time-series line chart. recharts LineChart on the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["LineChart"]


class LineChart(NudleRef):
    """Display-only chart ref accepting `store` (whole series) and `append`."""

    def store(self, value: Nu | dict) -> Nu:
        return Write(self, value)

    def append(self, x: Nu | float, y: Nu | float) -> Nu:
        return Append(self, x, y)
