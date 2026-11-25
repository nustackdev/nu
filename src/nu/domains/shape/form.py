"""What every shape surface shares: a slot-level surface laid beside a value surface.

A shape ref lays a capability surface (read, mutable, reactive) beside a value
surface from ``nu.surfaces`` (``StrSurface`` for a ``str`` slot). The capability
belongs to the slot, never to the value it holds, so a value read off a shape
ref drops back to the plain value form (``Str``): ``Surface._value_form`` finds
it through the value surface, past these capability bases.
"""

from __future__ import annotations

from nu.lang import Surface


__all__ = ["SlotSurface"]


class SlotSurface(Surface):
    """Base of every shape capability surface (``ItemSurface``, ``CollectionSurface`` and their tiers)."""
