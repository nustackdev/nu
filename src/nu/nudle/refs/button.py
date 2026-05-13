"""ButtonRef: click trigger. No value, just notifications.

`ButtonRef.clicked()` is the standard Change-style subscription; the
browser ships a `notify` frame on every click.
"""

from __future__ import annotations

from ..interactions.changed import Changed
from .base import NudleRef


__all__ = ["ButtonRef"]


class ButtonRef(NudleRef):
    """Click trigger; subscribe via `.clicked()`."""

    def clicked(self) -> Changed:
        return Changed(self)
