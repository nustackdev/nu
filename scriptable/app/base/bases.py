from scriptable.app.protocols import AppAsyncProtocol, AppCommonProtocol, AppSyncProtocol

from .common import AppCommonBase


class AppBase(AppCommonBase, AppCommonProtocol):
    pass


class AppSyncBase(AppBase, AppSyncProtocol):
    pass


class AppAsyncBase(AppBase, AppAsyncProtocol):
    pass


__all__ = [
    "AppAsyncBase",
    "AppSyncBase",
    "AppBase",
]
