"""UUID args."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from everyterm.term import Arg


if TYPE_CHECKING:
    pass


__all__ = [
    "UUIDArg",
]

type UUIDArg = Arg[UUID]
