class AsyncAppTasks:
    pass


# from __future__ import annotations

# from typing import TYPE_CHECKING, Any, Awaitable, Callable

# from loomi.app.base import AsyncApp
# from loomi.app.operations.ops_async import (
#     AppOperation,
#     ConditionalOperation,
#     DelayOperation,
#     FunctionOperation,
#     LoopOperation,
#     MapAppsOperation,
#     MapOperation,
#     ParallelOperation,
#     ReactiveMapAppsOperation,
#     ReactiveMapOperation,
#     RepeatOperation,
#     SequenceOperation,
#     WatchOperation,
# )

# from .base import AppCommonTasks
# from .protocols import AsyncOperationProtocol

# if TYPE_CHECKING:
#     from loomi.app.handlers.state import StatePath
#     from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol

# __all__ = [
#     "AsyncAppTasks",
# ]


# class AsyncAppTasks(AppCommonTasks, AsyncApp):
#     """
#     Service feature implementing operation capabilities.
#     """

#     async def start(self) -> None:
#         """Run the app."""
#         loc = await self.state.dict("_")
#         await self.execute(await self.run({}, loc), loc)

#     async def execute(
#         self,
#         op: AsyncOperationProtocol,
#         loc: "AsyncStateDictProtocol",
#     ) -> Any:
#         """Execute operation."""
#         return await op.execute(self, loc)

#     def function(self, func: Callable, *, name: str | None = None) -> AsyncOperationProtocol:
#         """Create function operation."""
#         return FunctionOperation(func, name=name)

#     def app(
#         self, app: AsyncApp, /, *, path: tuple[str, ...] | None = None
#     ) -> AsyncOperationProtocol:
#         """Create app operation."""
#         return AppOperation(app, path=path)

#     def sequence(
#         self,
#         op: AsyncOperationProtocol,
#         /,
#         *ops: AsyncOperationProtocol,
#         delay: float = 0,
#         continue_on_error: bool = False,
#     ) -> AsyncOperationProtocol:
#         """Create function operation."""
#         opserations = (op,) + ops
#         return SequenceOperation(
#             *opserations,
#             delay=delay,
#             continue_on_error=continue_on_error,
#         )

#     def repeat(
#         self,
#         op: AsyncOperationProtocol,
#         /,
#         *,
#         times: int | None = None,
#         while_key: str | tuple[str, ...] | None = None,
#         max_iterations: int | None = None,
#         delay: float = 0,
#         ignore_errors: bool = False,
#     ) -> AsyncOperationProtocol:
#         """Create repeat operation.

#         If neither times nor while_key is specified, the operation runs infinitely
#         (until max_iterations is reached, if specified).
#         """
#         return RepeatOperation(
#             operation=op,
#             times=times,
#             while_key=while_key,
#             max_iterations=max_iterations,
#             delay=delay,
#             ignore_errors=ignore_errors,
#         )

#     def parallel(
#         self,
#         op: AsyncOperationProtocol,
#         /,
#         *ops: AsyncOperationProtocol,
#         max_concurrent: int | None = None,
#         timeout: float | None = None,
#         ignore_errors: bool = False,
#     ) -> AsyncOperationProtocol:
#         """Create parallel operation."""
#         operations = (op,) + ops
#         return ParallelOperation(
#             *operations,
#             max_concurrent=max_concurrent,
#             timeout=timeout,
#             ignore_errors=ignore_errors,
#         )

#     def watch(
#         self,
#         op: AsyncOperationProtocol,
#         /,
#         *,
#         watch_key: StatePath,
#         depth: int = 0,
#         max_wait_time: float | None = None,
#         timeout_operation: AsyncOperationProtocol | None = None,
#     ) -> AsyncOperationProtocol:
#         """Create watch operation."""
#         return WatchOperation(
#             op,
#             watch_key=watch_key,
#             depth=depth,
#             max_wait_time=max_wait_time,
#             timeout_operation=timeout_operation,
#         )

#     def delay(
#         self,
#         op: AsyncOperationProtocol | None = None,
#         /,
#         *,
#         delay: float,
#     ) -> AsyncOperationProtocol:
#         """Create delay operation.

#         Executes the specified operation after waiting for the given delay period.
#         """
#         return DelayOperation(
#             op,
#             delay=delay,
#         )

#     def conditional(
#         self,
#         op: AsyncOperationProtocol,
#         /,
#         *,
#         condition_key: StatePath | None = None,
#         condition_func: Callable[["AsyncStateDictProtocol"], Awaitable[bool | Any]] | None = None,
#         else_operation: AsyncOperationProtocol | None = None,
#     ) -> AsyncOperationProtocol:
#         """Create conditional operation.

#         Executes the specified operation only if the condition evaluates to True.
#         The condition can be specified either by a state key or by a custom function.
#         Optionally executes an alternative operation if the condition is False.

#         Args:
#             operation: Operation to execute if condition is True
#             condition_key: State key to check for the condition
#             condition_func: Function that returns a boolean result
#             else_operation: Optional operation to execute if condition is False
#         """
#         return ConditionalOperation(
#             op,
#             condition_key=condition_key,
#             condition_func=condition_func,
#             else_operation=else_operation,
#         )

#     def map(
#         self,
#         op: "AsyncOperationProtocol",
#         /,
#         *,
#         items_key: str | tuple[str, ...],
#         max_concurrency: int | None = None,
#     ) -> AsyncOperationProtocol:
#         """Create map operation.

#         Executes the specified operation once for each item in a collection.
#         The collection is retrieved from the state using the specified items_key.
#         Each item is made available to the operation via the 'current_item' state key.
#         """
#         return MapOperation(
#             op,
#             items_key=items_key,
#             max_concurrency=max_concurrency,
#         )

#     def reactive_map(
#         self,
#         op: "AsyncOperationProtocol",
#         /,
#         *,
#         watch_key: "StatePath",
#         max_concurrency: int | None = None,
#         completion_operation: AsyncOperationProtocol | None = None,
#     ) -> AsyncOperationProtocol:
#         """Create reactive map operation.

#         This operation monitors a dictionary in the state and automatically applies
#         the specified operation to each item as it appears. It processes all existing items
#         on startup and then watches for new items to process them as they arrive.
#         Key deletions are tracked and logged but running tasks are not canceled.
#         """
#         return ReactiveMapOperation(
#             op,
#             watch_key=watch_key,
#             max_concurrency=max_concurrency,
#             completion_operation=completion_operation,
#         )

#     def map_apps(
#         self,
#         app: "AsyncApp",
#         /,
#         *apps: "AsyncApp",
#         items_key: str | tuple[str, ...],
#         max_concurrency: int | None = None,
#     ) -> AsyncOperationProtocol:
#         """Create map apps operation.

#         Executes given apps once for each item in a collection.
#         The collection is retrieved from the state using the specified items_key.
#         """
#         map_apps = list((app,) + apps)
#         return MapAppsOperation(
#             map_apps,
#             items_key=items_key,
#             max_concurrency=max_concurrency,
#         )

#     def reactive_map_apps(
#         self,
#         app: "AsyncApp",
#         /,
#         *apps: "AsyncApp",
#         watch_key: "StatePath",
#         max_concurrency: int | None = None,
#         completion_operation: AsyncOperationProtocol | None = None,
#     ) -> AsyncOperationProtocol:
#         """
#         Create reactive map apps operation.

#         This operation monitors a dictionary in the state and automatically applies
#         the specified apps to each item as it appears. It processes all existing items
#         on startup and then watches for new items to process them as they arrive.
#         Key deletions are tracked and logged but running tasks are not canceled.
#         """
#         map_apps = list((app,) + apps)
#         return ReactiveMapAppsOperation(
#             map_apps,
#             watch_key=watch_key,
#             max_concurrency=max_concurrency,
#             completion_operation=completion_operation,
#         )

#     def loop(
#         self,
#         op: AsyncOperationProtocol,
#         /,
#         *,
#         condition_key: StatePath | None = None,
#         condition_func: Callable[["AsyncStateDictProtocol"], Awaitable[bool | Any]] | None = None,
#         max_iterations: int | None = None,
#         delay: float = 0,
#         else_operation: AsyncOperationProtocol | None = None,
#     ) -> AsyncOperationProtocol:
#         """Create while operation.

#         Repeatedly executes the specified operation while the condition evaluates to True.
#         The condition can be specified either by a state key or by a custom function.
#         Optionally executes an alternative operation after the loop completes.

#         Args:
#             operation: Operation to execute while condition is True
#             condition_key: State key to check for the condition
#             condition_func: Function that returns a boolean result
#             max_iterations: Maximum number of iterations to prevent infinite loops
#             delay: Delay between iterations in seconds
#             else_operation: Optional operation to execute after the loop completes
#         """
#         return LoopOperation(
#             op,
#             condition_key=condition_key,
#             condition_func=condition_func,
#             max_iterations=max_iterations,
#             delay=delay,
#             else_operation=else_operation,
#         )
