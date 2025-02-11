from .handlers.initializer import AsyncAppInitializer, SyncAppInitializer
from .handlers.model import AsyncAppModel, SyncAppModel
from .handlers.services import AsyncAppServices, SyncAppServices
from .handlers.state import AsyncAppState, SyncAppState
from .handlers.tasks import AsyncAppTasks, SyncAppTasks


class AsyncApp(
    AsyncAppInitializer,
    AsyncAppState,
    AsyncAppTasks,
    AsyncAppServices,
    AsyncAppModel,
):
    pass


class SyncApp(
    SyncAppInitializer,
    SyncAppState,
    SyncAppTasks,
    SyncAppServices,
    SyncAppModel,
):
    pass


__all__ = ["AsyncApp", "SyncApp"]
