"""TypeBase — everybase kernel base for all typed refs.

TypeBase inherits from ObjectType (universal term-algebra methods)
and serves as the everybase-specific identity marker.

Substrate-specific bases (PyRef, PVRefBase) implement fetch().
Type-specific bases (IntType, etc.) add operator traits.
"""

from __future__ import annotations

from .object import ObjectType


__all__ = [
    "TypeBase",
]


class TypeBase[T](ObjectType):
    """Abstract base for all typed refs.

    Inherits from ObjectType (sentinel checks) and provides
    everybase-specific kernel identity.

    Subclasses (IntType, etc.) add operator traits.
    Substrate-specific bases (PyRef, PVRefBase) add storage.

    Note: Arithmetic operations return Python memory refs because
    the result is a computation (lazy expression), not a storage
    location. A PVIntRef + 5 produces IntValue(AddOp(...)).
    """

    pass
