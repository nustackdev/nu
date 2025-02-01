from .handlers.state.state_async import AppState as AppAsyncState
from .handlers.tasks.tasks_async import AppTasks as AppAsyncTasks


class AsyncApp(
    AppAsyncState,
    AppAsyncTasks,
):
    pass


class SyncApp:
    pass


__all__ = ["AsyncApp"]
