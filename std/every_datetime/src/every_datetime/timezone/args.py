"""Timezone args."""

from __future__ import annotations

from datetime import timezone
from typing import TYPE_CHECKING

from every._abc import Arg


if TYPE_CHECKING:
    from .type import TimezoneType


__all__ = [
    "TimezoneArg",
]

type TimezoneArg = Arg[timezone | TimezoneType]
