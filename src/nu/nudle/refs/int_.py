"""IntRef: integer cell. Renders as <span>."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["IntRef"]


class IntRef(NudleRef):
    """Display-only int ref."""

    def store(self, value: Nu | int) -> Nu:
        return Write(self, value)
