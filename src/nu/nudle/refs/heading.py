"""HeadingRef: in-body heading. Renders as <h1>."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["HeadingRef"]


class HeadingRef(NudleRef):
    """Display-only string ref. Body heading."""

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)
