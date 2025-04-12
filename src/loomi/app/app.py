from .composer import AsyncAppComposer, SyncAppComposer
from .execution_handler import AsyncAppExecutionHandler, SyncAppExecutionHandler
from .initializer import AsyncAppInitializer, SyncAppInitializer
from .meta import AppMeta
from .service_handler import AsyncAppServicesHandler, SyncAppServicesHandler
from .state_handler import AsyncCommonAppStateHandler, SyncCommonAppStateHandler

__all__ = [
    "AsyncApp",
    "SyncApp",
    "App",
]


class AsyncApp(
    AsyncAppInitializer,
    AsyncCommonAppStateHandler,
    AsyncAppExecutionHandler,
    AsyncAppServicesHandler,
    AsyncAppComposer,
    metaclass=AppMeta,
):
    pass


class SyncApp(
    SyncAppInitializer,
    SyncCommonAppStateHandler,
    SyncAppExecutionHandler,
    SyncAppServicesHandler,
    SyncAppComposer,
    metaclass=AppMeta,
):
    pass


App = AsyncApp | SyncApp
