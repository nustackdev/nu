"""PieChart: pie / donut chart from (label, value) slices. recharts on the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import DictForm

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["PieChart"]


DEFAULT_COLORS: list[str] = [
    "#2563eb",
    "#16a34a",
    "#f59e0b",
    "#dc2626",
    "#7c3aed",
    "#0891b2",
    "#db2777",
    "#65a30d",
]


class PieChart(NudleRef):
    """Display-only pie chart ref. `write` (partial) and `append` (one slice)."""

    slices: ClassVar[list] = []
    colors: ClassVar[list[str]] = DEFAULT_COLORS
    inner_radius: ClassVar[float] = 0.0
    show_labels: ClassVar[bool] = True
    show_legend: ClassVar[bool] = True
    total_label: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "slices": list(cls.slices),
            "colors": list(cls.colors),
            "inner_radius": cls.inner_radius,
            "show_labels": cls.show_labels,
            "show_legend": cls.show_legend,
            "total_label": cls.total_label,
        }

    def store_slices(self, slices: Nu | list) -> Nu:
        return Write(self, DictForm.of(slices=slices))

    def store_colors(self, colors: Nu | list) -> Nu:
        return Write(self, DictForm.of(colors=colors))

    def store_inner_radius(self, value: Nu | float) -> Nu:
        return Write(self, DictForm.of(inner_radius=value))

    def store_show_labels(self, value: Nu | bool) -> Nu:
        return Write(self, DictForm.of(show_labels=value))

    def store_show_legend(self, value: Nu | bool) -> Nu:
        return Write(self, DictForm.of(show_legend=value))

    def store_total_label(self, value: Nu | str) -> Nu:
        return Write(self, DictForm.of(total_label=value))

    def clear(self) -> Nu:
        return Write(self, DictForm.of(slices=[]))

    def store(
        self,
        slices: Nu | list | dict | None = None,
        colors: Nu | list | None = None,
        inner_radius: Nu | float | None = None,
        show_labels: Nu | bool | None = None,
        show_legend: Nu | bool | None = None,
        total_label: Nu | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if slices is not None:
            # legacy: store({"slices": [...]}) keeps working.
            if isinstance(slices, dict) and "slices" in slices:
                payload["slices"] = slices["slices"]
            else:
                payload["slices"] = slices
        if colors is not None:
            payload["colors"] = colors
        if inner_radius is not None:
            payload["inner_radius"] = inner_radius
        if show_labels is not None:
            payload["show_labels"] = show_labels
        if show_legend is not None:
            payload["show_legend"] = show_legend
        if total_label is not None:
            payload["total_label"] = total_label
        return Write(self, DictForm.of(**payload))

    def append(self, label: Nu | str, value: Nu | float) -> Nu:
        return Append(self, label, value)
