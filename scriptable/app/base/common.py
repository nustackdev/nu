from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scriptable.service import Service


__all__ = [
    "AppCommon",
]


class AppCommon:
    _services: dict[str, "Service"]

    def __init__(self):
        self._services = {}

    @property
    def key(self) -> str:
        return str(id(self))[:12]

    @property
    def readable_name(self) -> str:
        return f"{self.__class__.__name__}"
