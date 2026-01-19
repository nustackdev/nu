"""UUID type for Shape system.

Provides UUIDType, UUIDRef, and UUIDSlot for working with
Python UUID objects.

Example:
    from everybase.type import UUIDSlot

    class Entity(Shape):
        id = UUIDSlot()
        parent_id = UUIDSlot()

    # Operations
    Entity.id.set(uuid4())
    Entity.id.get().hex()
"""

from __future__ import annotations

from .args import UUIDArg
from .ref import UUIDRef
from .slot import UUIDSlot
from .type import UUIDType


__all__ = [
    "UUIDType",
    "UUIDRef",
    "UUIDArg",
    "UUIDSlot",
]
