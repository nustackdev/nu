"""Sparkline: small inline trend line, no axes. recharts LineChart on the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.queries.record import Record

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["Sparkline"]


class Sparkline(NudleRef):
    """Display-only inline trend line. `write` (partial) and `append` (one point)."""

    color: ClassVar[str] = "#2563eb"
    height: ClassVar[int] = 32
    max_points: ClassVar[int] = 100

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "color": cls.color,
            "height": cls.height,
            "max_points": cls.max_points,
        }

    def store_points(self, points: Nu | list) -> Nu:
        return Write(self, Record(points=points))

    def store_color(self, value: Nu | str) -> Nu:
        return Write(self, Record(color=value))

    def store_height(self, value: Nu | int) -> Nu:
        return Write(self, Record(height=value))

    def store_max_points(self, value: Nu | int) -> Nu:
        return Write(self, Record(max_points=value))

    def clear(self) -> Nu:
        return Write(self, Record(points=[]))

    def store(
        self,
        points: Nu | list | dict | None = None,
        color: Nu | str | None = None,
        height: Nu | int | None = None,
        max_points: Nu | int | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if points is not None:
            if isinstance(points, dict) and "points" in points:
                payload["points"] = points["points"]
            else:
                payload["points"] = points
        if color is not None:
            payload["color"] = color
        if height is not None:
            payload["height"] = height
        if max_points is not None:
            payload["max_points"] = max_points
        return Write(self, Record(**payload))

    def append(self, x: Nu | float, y: Nu | float) -> Nu:
        return Append(self, x, y)
