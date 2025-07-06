"""
Reactive operation execution engine.

This module provides execution capabilities for reactive operations such as
Subscribe, which execute operations in response to state changes.
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from typing import Any, Dict, Tuple

from loomi.state.interface.tree import AsyncStateProtocol, SyncStateProtocol
from loomi.state.interface.type_vars import StateT

from ..context import Context
from ..operations import Operation, Subscribe
from .base import EngineBase
from .exceptions import OperationExecutionError, StateAccessError


class ReactiveEngine(EngineBase[StateT]):
    """
    Engine mixin for executing reactive operations.

    Provides implementation for executing operations like Subscribe that
    react to state changes.
    """

    async def setup_reactive(self) -> None:
        """
        Setup the reactive engine.
        This method initializes the reactive engine and prepares it for
        executing reactive operations.
        """
        # Track active subscriptions for cleanup
        self._active_subscriptions: Dict[str, asyncio.Task] = {}
        # Event flags to signal when a change has occurred for once=True subscriptions
        self._change_events: Dict[str, asyncio.Event] = {}

    async def cleanup_reactive(self) -> None:
        """
        Clean up all reactive engine resources.

        This method cancels all active subscriptions and should be called
        during engine shutdown.
        """
        await self.cancel_all_subscriptions()

        # Clear change events
        self._change_events.clear()

    async def exec_subscribe(self, operation: Subscribe[StateT], context: Context[StateT]) -> None:
        """
        Execute a Subscribe operation.

        Sets up a subscription to watch for state changes and executes
        the specified operation when changes occur.

        Args:
            operation: The Subscribe operation to execute
            context: The execution context

        Raises:
            OperationExecutionError: If there's an error during execution
        """
        watch_path = operation.watch_path
        depth = operation.depth
        once = operation.once
        max_concurrency = operation.max_concurrency
        subscribe_op = operation.subscribe_op

        self.logger.debug(
            f"Setting up Subscribe operation watching path={watch_path}, "
            f"depth={depth}, once={once}, max_concurrency={max_concurrency}"
        )

        # Generate a unique ID for this subscription
        subscription_id = str(uuid.uuid4())

        # Create a semaphore for concurrency control if needed
        semaphore = None
        if max_concurrency > 0:
            semaphore = asyncio.Semaphore(max_concurrency)

        # Create an event for signaling when a change has been processed
        # This is used for once=True subscriptions
        if once:
            self._change_events[subscription_id] = asyncio.Event()

        # Define the callback function that will be called when state changes
        async def on_change(change_path: Tuple[str, ...]) -> None:
            """Callback for state changes."""
            self.logger.debug(f"Subscribe detected change at {change_path}")

            # Execute with semaphore control if enabled
            if semaphore:
                async with semaphore:
                    await self._handle_subscribe_change(
                        subscription_id, operation, context, subscribe_op, change_path
                    )
            else:
                await self._handle_subscribe_change(
                    subscription_id, operation, context, subscribe_op, change_path
                )

            # If once=True, signal the event that a change has been processed
            if once and subscription_id in self._change_events:
                self.logger.debug(
                    "Subscribe operation with once=True processed a change, signaling completion"
                )
                self._change_events[subscription_id].set()

        try:
            # Create the subscription

            if isinstance(self.state, AsyncStateProtocol):
                state = await self.state.at(*watch_path)
                subscription = await state.subscribe(on_change, depth=depth)
            elif isinstance(self.state, SyncStateProtocol):
                if inspect.iscoroutinefunction(on_change):
                    # Wrap the callback in a coroutine if needed
                    raise ValueError(
                        "on_change callback cannot be a coroutine function when state.subscribe is not async"
                    )
                else:
                    subscription = self.state.at(*watch_path).subscribe(on_change, depth=depth)
            else:
                raise StateAccessError(
                    f"Unsupported state type: {type(self.state)}",
                    operation=operation,
                )

            # Create a task to manage the subscription
            task = asyncio.create_task(
                self._manage_subscription(subscription_id, subscription, operation)
            )

            # Store the task for cleanup
            self._active_subscriptions[subscription_id] = task

            # Wait for the task to complete
            await task

        except Exception as e:
            error_msg = f"Error in Subscribe operation: {str(e)}"
            self.logger.error(error_msg, exc_info=e)
            raise OperationExecutionError(error_msg, operation=operation, context=context, cause=e)
        finally:
            # Clean up the change event if it exists
            if subscription_id in self._change_events:
                del self._change_events[subscription_id]

    async def _handle_subscribe_change(
        self,
        subscription_id: str,
        operation: Subscribe[StateT],
        parent_context: Context[StateT],
        subscribe_op: Operation[StateT],
        change_path: Tuple[str, ...],
    ) -> None:
        """
        Handle a state change for a Subscribe operation.

        Args:
            subscription_id: Unique ID for this subscription
            operation: The Subscribe operation
            parent_context: The parent context
            subscribe_op: The operation to execute
            change_path: The path where the change occurred
        """
        self.logger.debug(f"Handling change at {change_path} for Subscribe operation")

        try:
            # # Create context for this execution
            change_context = parent_context.derive(operation=subscribe_op)

            # Add change metadata to context
            change_context["change_path"] = change_path

            # Execute the operation
            await self.exec_operation(change_context)

        except Exception as e:
            error_msg = f"Error handling change at {change_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=e)

            # Handle error based on error behavior
            if operation._error_behavior == "fail":
                raise OperationExecutionError(
                    error_msg, operation=operation, context=parent_context, cause=e
                )

    async def _manage_subscription(
        self,
        subscription_id: str,
        subscription: Any,
        operation: Subscribe[StateT],
    ) -> None:
        """
        Manage the lifecycle of a subscription.

        This task runs for the duration of the subscription and handles
        cleanup when the subscription is done.

        Args:
            subscription_id: Unique ID for this subscription
            subscription: The state subscription object
            operation: The Subscribe operation
        """
        try:
            if operation.once:
                # For once=True, wait for the change event to be set
                if subscription_id in self._change_events:
                    self.logger.debug(
                        f"Waiting for first change for subscription {subscription_id}"
                    )
                    await self._change_events[subscription_id].wait()
                    self.logger.debug(
                        f"First change detected for subscription {subscription_id}, completing"
                    )
                else:
                    # This shouldn't happen, but handle it gracefully
                    self.logger.warning(
                        f"Missing change event for once=True subscription {subscription_id}"
                    )
                    # Wait a bit in case the event is created late
                    await asyncio.sleep(1.0)
            else:
                # For continuous subscriptions, run until cancelled
                self.logger.debug(
                    f"Continuous subscription {subscription_id} running until cancelled"
                )
                await asyncio.Future()

        except asyncio.CancelledError:
            self.logger.warning(f"Subscription {subscription_id} cancelled")
            # Allow the cancellation to propagate after cleanup

        finally:
            # Clean up the subscription
            await self._cleanup_subscription(subscription_id, subscription)

    async def _cleanup_subscription(self, subscription_id: str, subscription: Any) -> None:
        """
        Clean up a subscription.

        Args:
            subscription_id: Unique ID for this subscription
            subscription: The state subscription object
        """
        self.logger.debug(f"Cleaning up subscription {subscription_id}")

        # Remove from active subscriptions
        if subscription_id in self._active_subscriptions:
            del self._active_subscriptions[subscription_id]

        # Unsubscribe from state
        try:
            if isinstance(self.state, AsyncStateProtocol):
                await self.state.unsubscribe(subscription)

            elif isinstance(self.state, SyncStateProtocol):
                self.state.unsubscribe(subscription)

            else:
                raise StateAccessError(f"Unsupported state type: {type(self.state)}")

        except Exception as e:
            self.logger.error(f"Error unsubscribing: {e}", exc_info=e)

    async def cancel_all_subscriptions(self) -> None:
        """
        Cancel all active subscriptions.

        This method is typically called during shutdown to ensure all
        subscriptions are properly cleaned up.
        """
        self.logger.debug(f"Cancelling {len(self._active_subscriptions)} active subscriptions")

        # Cancel all active subscription tasks
        for subscription_id, task in list(self._active_subscriptions.items()):
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete
        if self._active_subscriptions:
            await asyncio.gather(
                *[task for task in self._active_subscriptions.values()], return_exceptions=True
            )

        # Clear the dictionary
        self._active_subscriptions.clear()
