from .handlers.services.services_async import AppServices as AppAsyncServices
from .handlers.state.state_async import AppState as AppAsyncState
from .handlers.tasks.tasks_async import AppTasks as AppAsyncTasks


class AsyncApp(
    AppAsyncState,
    AppAsyncTasks,
    AppAsyncServices,
):
    pass


class SyncApp:
    pass


__all__ = ["AsyncApp", "SyncApp"]
