from .handlers.initializer.initializer_async import AppInitializer as AppAsyncInitializer
from .handlers.initializer.initializer_sync import AppInitializer as AppSyncInitializer
from .handlers.model.model_async import AppModel as AppAsyncModel
from .handlers.services.services_async import AppServices as AppAsyncServices
from .handlers.services.services_sync import AppServices as AppSyncServices
from .handlers.state.state_async import AppState as AppAsyncState
from .handlers.state.state_sync import AppState as AppSyncState
from .handlers.tasks.tasks_async import AppTasks as AppAsyncTasks


class AsyncApp(
    AppAsyncInitializer,
    AppAsyncState,
    AppAsyncTasks,
    AppAsyncServices,
    AppAsyncModel,
):
    pass


class SyncApp(
    AppSyncInitializer,
    AppSyncState,
    AppSyncServices,
):
    pass


__all__ = ["AsyncApp", "SyncApp"]
