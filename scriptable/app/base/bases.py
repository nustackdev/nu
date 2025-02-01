from typing import TYPE_CHECKING

from scriptable.app.protocols import AppAsyncProtocol, AppCommonProtocol, AppSyncProtocol

from .common import AppCommonBase

if TYPE_CHECKING:
    from scriptable.service import AsyncService, SyncService


class AppBase(AppCommonBase, AppCommonProtocol):
    pass


class AppSyncBase(AppBase, AppSyncProtocol):
    def __init__(self):
        super().__init__()

        self._services: dict[str, "SyncService"] = {}


class AppAsyncBase(AppBase, AppAsyncProtocol):
    def __init__(self):
        super().__init__()

        self._services: dict[str, "AsyncService"] = {}


__all__ = [
    "AppAsyncBase",
    "AppSyncBase",
    "AppBase",
]
