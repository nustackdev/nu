from .handlers.initializer import AsyncAppInitializer, SyncAppInitializer
from .handlers.model import AsyncAppModel, SyncAppModel
from .handlers.services import AsyncAppServices, SyncAppServices
from .handlers.state import AsyncAppState, SyncAppState
from .handlers.tasks import AsyncAppTasks, SyncAppTasks

__all__ = ["AsyncApp", "SyncApp"]

class AsyncApp(
    AsyncAppInitializer, AsyncAppState, AsyncAppTasks, AsyncAppServices, AsyncAppModel
): ...
class SyncApp(SyncAppInitializer, SyncAppState, SyncAppTasks, SyncAppServices, SyncAppModel): ...
