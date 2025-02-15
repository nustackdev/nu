import abc

from loomi.app.protocols import AppProtocol, AsyncAppProtocol, SyncAppProtocol

from .common import AppCommon

__all__ = ["SyncApp", "AsyncApp", "App"]

class App(AppCommon, AppProtocol): ...
class SyncApp(App, SyncAppProtocol, metaclass=abc.ABCMeta): ...
class AsyncApp(App, AsyncAppProtocol, metaclass=abc.ABCMeta): ...
