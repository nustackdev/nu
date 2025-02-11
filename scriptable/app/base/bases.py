from __future__ import annotations

from typing import TYPE_CHECKING

from scriptable.app.protocols import AppProtocol, AsyncAppProtocol, SyncAppProtocol

from .common import AppCommon

if TYPE_CHECKING:
    from scriptable.service import AsyncService, SyncService

__all__ = [
    "SyncApp",
    "AsyncApp",
    "App",
]


class App(AppCommon, AppProtocol):
    pass


class SyncApp(App, SyncAppProtocol):
    _services: dict[str, "SyncService"]


class AsyncApp(App, AsyncAppProtocol):
    _services: dict[str, "AsyncService"]
