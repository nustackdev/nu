"""NullSurface: the (empty) method layer of the ``NullForm`` node."""

from __future__ import annotations

from nu.lang import Surface


__all__ = [
    "NullSurface",
]


class NullSurface(Surface):
    """The methods of ``NullForm``. No slot holds one, so only the form carries them."""
