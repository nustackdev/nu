"""Type argument aliases for UUID types."""

from __future__ import annotations

from uuid import UUID

from nu import Arg


__all__ = [
    "UUIDArg",
]

type UUIDArg = Arg[UUID | str]
