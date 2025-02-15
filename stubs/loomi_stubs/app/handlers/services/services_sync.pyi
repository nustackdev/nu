import abc

from loomi.app.base import SyncApp

from .base import AppCommonServices

__all__ = ["SyncAppServices"]

class SyncAppServices(AppCommonServices, SyncApp, metaclass=abc.ABCMeta):
    def initialize_services(self) -> None: ...
    def shutdown_services(self) -> None: ...
