from .base import AppMeta
from .handlers.initializer import AsyncAppInitializer, SyncAppInitializer
from .handlers.model import AsyncAppModel, SyncAppModel
from .handlers.services import AsyncAppServices, SyncAppServices
from .handlers.state import AsyncAppState, SyncAppState
from .handlers.tasks import AsyncAppTasks, SyncAppTasks

__all__ = [
    "AsyncApp",
    "SyncApp",
]


class AsyncApp(
    AsyncAppInitializer,
    AsyncAppState,
    AsyncAppTasks,
    AsyncAppServices,
    AsyncAppModel,
    metaclass=AppMeta,
):
    pass


class SyncApp(
    SyncAppInitializer,
    SyncAppState,
    SyncAppTasks,
    SyncAppServices,
    SyncAppModel,
    metaclass=AppMeta,
):
    pass
