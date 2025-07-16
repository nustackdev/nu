# """
# ReactiveMap operation.

# This module provides the ReactiveMap function, which creates a compound operation that:
# 1. First processes all existing items in the collection.
# 2. Then establishes a subscription to watch for changes. When new items are added,
#     it automatically applies the operation to them.
# """

# from __future__ import annotations

# from loomi.evaluator.interface.evaluator import AsyncEvaluatorProtocol, SyncEvaluatorProtocol
# from loomi.evaluator.interface.type_vars import (
#     AppOperationT,
#     AsyncEvaluatorT_co,
#     BranchOperationT,
#     ContextT_contra,
#     DelayOperationT,
#     FunctionOperationT,
#     LoopOperationT,
#     MapOperationT,
#     OperationT_contra,
#     ParallelOperationT,
#     RetryOperationT,
#     SequenceOperationT,
#     SubscribeOperationT,
#     SyncContextT_contra,
#     SyncEvaluatorT_co,
#     TimeoutOperationT,
# )
# from loomi.evaluator.interface.types import ErrorBehavior

# __all__ = [
#     "ReactiveMap",
# ]


# def ReactiveMap(
#     executor: (
#         AsyncEvaluatorProtocol[
#             AsyncEvaluatorT_co,
#             ContextT_contra,
#             OperationT_contra,
#             AppOperationT,
#             BranchOperationT,
#             DelayOperationT,
#             FunctionOperationT,
#             LoopOperationT,
#             MapOperationT,
#             ParallelOperationT,
#             RetryOperationT,
#             SequenceOperationT,
#             SubscribeOperationT,
#             TimeoutOperationT,
#         ]
#         | SyncEvaluatorProtocol[
#             SyncEvaluatorT_co,
#             SyncContextT_contra,
#             OperationT_contra,
#             AppOperationT,
#             BranchOperationT,
#             DelayOperationT,
#             FunctionOperationT,
#             LoopOperationT,
#             MapOperationT,
#             ParallelOperationT,
#             RetryOperationT,
#             SequenceOperationT,
#             SubscribeOperationT,
#             TimeoutOperationT,
#         ]
#     ),
#     op: OperationT_contra,
#     /,
#     *,
#     items_path: tuple[str, ...] | str,
#     max_concurrency: int = 1,
#     error_behavior: ErrorBehavior = "fail",
#     on_fail: OperationT_contra | None = None,
# ) -> SequenceOperationT:
#     """
#     ReactiveMap compound operation.

#     Create a compound operation that continuously maps an operation to new items
#     in a collection as they are added.

#     This operation first processes all existing items in the collection,
#     then establishes a subscription to watch for changes. When new items
#     are added, it automatically applies the operation to them.

#     Args:
#         op: The operation to apply to each item
#         items_path: Path to the collection in state
#         max_concurrency: Maximum number of concurrent operations
#         error_behavior: How to handle errors that occur during execution
#         on_fail: Operation to execute when an error occurs

#     Returns:
#         A compound operation that implements the reactive mapping behavior
#     """
#     if not items_path:
#         raise ValueError("items_path must be provided")

#     if max_concurrency < -1:
#         raise ValueError(f"Invalid max_concurrency: {max_concurrency}. Must be >= -1")

#     # Normalize items_path to tuple
#     if isinstance(items_path, str):
#         items_path = (items_path,)

#     # Set up a registry to track processed keys
#     processed_keys = set()

#     # Define a wrapper function that updates our registry
#     async def process_item(context: ContextT_contra):
#         """Process a single item and track it in our registry."""
#         # Get the key from the context (added by Map operation)
#         key = context["map_key"]

#         # Add this key to our processed set
#         processed_keys.add(key)

#     # Define a change handler function
#     async def handle_change(context: ContextT_contra):
#         """Handle collection changes and process new items."""
#         # Extract change information
#         change_path = context["change_path"]

#         # The last element of the path is the key that changed
#         if len(change_path) != len(items_path) + 1:
#             raise ValueError(
#                 f"Invalid change path length: {len(change_path)}. "
#                 f"Expected {len(items_path) + 1}"
#             )

#         # Get the key that changed
#         key = change_path[-1]

#         if key not in processed_keys:
#             # New item added - process it

#             if hasattr(executor, "logger"):
#                 executor.logger.debug(f"New item added at key {key}, processing")  # type: ignore

#             # Track this key as processed
#             processed_keys.add(key)

#         elif key in processed_keys:
#             # Existing item updated - just log
#             if hasattr(executor, "logger"):
#                 executor.logger.debug(f"Item at key {key} was updated, not reprocessing")  # type: ignore

#     # First map over all existing items
#     initial_map = executor.Map(
#         executor.Sequence(
#             executor.Function(process_item),
#             op,
#         ),
#         items_path=items_path,
#         max_concurrency=max_concurrency,
#         error_behavior=error_behavior,
#         on_fail=on_fail,
#     )

#     # Then subscribe to changes
#     subscription = executor.Subscribe(
#         executor.Sequence(
#             executor.Function(handle_change),
#             op,
#         ),
#         watch_path=items_path,
#         depth=1,  # Only watch direct children
#         error_behavior=error_behavior,
#         on_fail=on_fail,
#     )

#     # Return a sequence that does both
#     return executor.Sequence(
#         initial_map,
#         subscription,
#         error_behavior=error_behavior,
#         on_fail=on_fail,
#     )
