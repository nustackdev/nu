"""TableRef: rows of dicts. Display-only; column order taken from first row."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["TableRef"]


class TableRef(NudleRef):
    """Display-only table. Value is list[dict[str, Any]]."""

    def store(self, rows: Nu | list[dict[str, Any]]) -> Nu:
        return Write(self, rows)
