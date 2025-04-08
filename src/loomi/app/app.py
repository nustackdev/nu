from .base import AppMeta
from .composer import AsyncAppComposer, SyncAppComposer
from .initializer import AsyncAppInitializer, SyncAppInitializer
from .services import AsyncAppServices, SyncAppServices
from .state import AsyncAppState, SyncAppState
from .tasks import AsyncAppTasks, SyncAppTasks

__all__ = [
    "AsyncApp",
    "SyncApp",
]


class AsyncApp(
    AsyncAppInitializer,
    AsyncAppState,
    AsyncAppTasks,
    AsyncAppServices,
    AsyncAppComposer,
    metaclass=AppMeta,
):
    pass


class SyncApp(
    SyncAppInitializer,
    SyncAppState,
    SyncAppTasks,
    SyncAppServices,
    SyncAppComposer,
    metaclass=AppMeta,
):
    pass
