from .composer import AsyncAppComposer, SyncAppComposer
from .execution_handler import AsyncAppExecutionHandler, SyncAppExecutionHandler
from .initializer import AsyncAppInitializer, SyncAppInitializer
from .meta import AppMeta
from .service_handler import AsyncAppServicesHandler, SyncAppServicesHandler
from .state_handler import AsyncCommonAppStateHandler, SyncCommonAppStateHandler
from .types import ET, ST, SyncET, SyncST

__all__ = [
    "AsyncApp",
    "SyncApp",
    "App",
]


class AsyncApp(
    AsyncAppInitializer[ST, ET],
    AsyncCommonAppStateHandler[ST, ET],
    AsyncAppExecutionHandler[ST, ET],
    AsyncAppServicesHandler[ST, ET],
    AsyncAppComposer[ST, ET],
    metaclass=AppMeta,
):
    pass


class SyncApp(
    SyncAppInitializer[SyncST, SyncET],
    SyncCommonAppStateHandler[SyncST, SyncET],
    SyncAppExecutionHandler[SyncST, SyncET],
    SyncAppServicesHandler[SyncST, SyncET],
    SyncAppComposer[SyncST, SyncET],
    metaclass=AppMeta,
):
    pass


App = AsyncApp | SyncApp
