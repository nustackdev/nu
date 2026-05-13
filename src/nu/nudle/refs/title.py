"""TitleRef: page title or section heading. Renders as <h1>."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["TitleRef"]


class TitleRef(NudleRef):
    """Display-only string ref."""

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)
