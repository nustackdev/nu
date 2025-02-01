from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scriptable.service import Service


class AppCommonBase:
    def __init__(self):
        self._services: dict[str, "Service"] = {}

    @property
    def key(self) -> str:
        return str(id(self))[:12]

    @property
    def readable_name(self) -> str:
        return f"{self.__class__.__name__}"


__all__ = [
    "AppCommonBase",
]
