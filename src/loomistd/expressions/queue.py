from __future__ import annotations

import threading

from loomi.expression import Context, Expression, ExpressionError, ExpressionPath, ExpressionValue
from loomistd.app import SyncAppProtocol
from loomistd.views.queue import QueueView

__all__ = [
    "Enqueue",
    "Dequeue",
    "Peek",
    "ClearQueue",
]


class Queue(Expression[SyncAppProtocol]):
    """
    Add an item to the back of a queue.

    This expression adds a value to the end of a queue at the specified path.
    If the queue doesn't exist, it will be created automatically.

    Args:
        path: State path to the queue (e.g., ("work_queue",) or ("tasks", "pending"))
        value: Value to enqueue (can be direct value or state path)

    Examples:
        ```python
        # Enqueue direct value
        Enqueue(self, ("work_queue",), "process_order_123")

        # Enqueue from state path
        Enqueue(self, ("tasks", "pending"), Path().current_job)

        # Enqueue complex object
        Enqueue(self, ("notifications",), {
            "type": "email",
            "recipient": "user@example.com",
            "subject": "Welcome!"
        })
        ```
    """

    def __init__(self, app, path: ExpressionPath, **kwargs):
        super().__init__(app, **kwargs)
        self.path = path

    def do_evaluate(self, context: "Context") -> None:
        """Add value to back of queue using unified infrastructure."""
        with self.app.state.tree.transaction() as transaction:
            # Get queue view at the specified path
            view, path = self._resolve_path(self.path, self.app.state.tree, transaction, context)
            queue_view = view.view(str(path), QueueView)
            queue_view.is_empty()  # Ensure the queue exists. FIXME: Add init method or make this implicit

            print(queue_view)


class Enqueue(Expression[SyncAppProtocol]):
    """
    Add an item to the back of a queue.

    This expression adds a value to the end of a queue at the specified path.
    If the queue doesn't exist, it will be created automatically.

    Args:
        path: State path to the queue (e.g., ("work_queue",) or ("tasks", "pending"))
        value: Value to enqueue (can be direct value or state path)

    Examples:
        ```python
        # Enqueue direct value
        Enqueue(self, ("work_queue",), "process_order_123")

        # Enqueue from state path
        Enqueue(self, ("tasks", "pending"), Path().current_job)

        # Enqueue complex object
        Enqueue(self, ("notifications",), {
            "type": "email",
            "recipient": "user@example.com",
            "subject": "Welcome!"
        })
        ```
    """

    def __init__(self, app, path: ExpressionPath, value: ExpressionValue, **kwargs):
        super().__init__(app, **kwargs)
        self.path = path
        self.value = value

    def do_evaluate(self, context: "Context") -> None:
        """Add value to back of queue using unified infrastructure."""
        with self.app.state.tree.transaction() as transaction:
            # Get queue view at the specified path
            view, path = self._resolve_path(self.path, self.app.state.tree, transaction, context)
            queue_view = view.view(str(path), QueueView)

            queue_view.is_empty()  # Ensure the queue exists. TODO: Add init method or make this implicit

            # Resolve the value to enqueue
            value = self._resolve_value(self.value, self.app.state.tree, transaction, context)

            # Enqueue the value
            try:
                queue_view.enqueue(value)
            except Exception as e:
                raise ExpressionError(
                    f"Failed to enqueue value at path {self.path}: {e}",
                    expression=self,
                    cause=e,
                )


class Dequeue(Expression[SyncAppProtocol]):
    """
    Remove and return the front item from a queue.

    This expression removes the first item from the queue (FIFO) and optionally
    stores it at a specified state path.

    Args:
        path: State path to the queue (e.g., ("work_queue",) or ("tasks", "pending"))
        store_at: Optional state path where to store the dequeued value

    Examples:
        ```python
        # Simple dequeue (just remove)
        Dequeue(self, ("work_queue",))

        # Dequeue and store result
        Dequeue(self, ("work_queue",), store_at=("current_task",))

        # Dequeue and store in nested path
        Dequeue(self, ("notifications",), store_at=("processing", "current_notification"))
        ```
    """

    def __init__(
        self, app, path: ExpressionPath, *, store_at: ExpressionPath | None = None, **kwargs
    ):
        super().__init__(app, **kwargs)
        self.path = path
        self.store_at = store_at

    def do_evaluate(self, context: "Context") -> None:
        """Remove front item from queue and optionally store it."""
        with self.app.state.tree.transaction() as transaction:
            # Get queue view at the specified path
            view, path = self._resolve_path(self.path, self.app.state.tree, transaction, context)
            queue_view = view.view(str(path), QueueView)

            # Dequeue the value
            try:
                dequeued_value = queue_view.dequeue()
            except Exception as e:
                raise ExpressionError(
                    f"Failed to dequeue value from path {self.path}: {e}",
                    expression=self,
                    cause=e,
                )

            # Store the dequeued value if store_at is specified
            if self.store_at is not None:
                store_view, store_path = self._resolve_path(
                    self.store_at, self.app.state.tree, transaction, context
                )
                try:
                    store_view.set(store_path, dequeued_value)  # type: ignore
                except Exception as e:
                    raise ExpressionError(
                        f"Failed to store dequeued value at path {self.store_at}: {e}",
                        expression=self,
                        cause=e,
                    )


class Peek(Expression[SyncAppProtocol]):
    """
    Look at the front item of a queue without removing it.

    This expression examines the first item in the queue (FIFO) without removing it
    and optionally stores it at a specified state path.

    Args:
        path: State path to the queue (e.g., ("work_queue",) or ("tasks", "pending"))
        store_at: Optional state path where to store the peeked value

    Examples:
        ```python
        # Simple peek (just look, don't store)
        Peek(self, ("work_queue",))

        # Peek and store result
        Peek(self, ("work_queue",), store_at=("next_task",))

        # Peek and store in nested path
        Peek(self, ("notifications",), store_at=("preview", "next_notification"))
        ```
    """

    def __init__(
        self, app, path: ExpressionPath, *, store_at: ExpressionPath | None = None, **kwargs
    ):
        super().__init__(app, **kwargs)
        self.path = path
        self.store_at = store_at

    def do_evaluate(self, context: "Context") -> None:
        """Look at front item of queue without removing it."""
        # Use snapshot for read-only operation when not storing
        if self.store_at is None:
            with self.app.state.tree.snapshot() as snapshot:
                view, path = self._resolve_path(self.path, self.app.state.tree, snapshot, context)
                queue_view = view.view(str(path), QueueView)
                try:
                    queue_view.peek()  # Just peek, don't store anywhere
                except Exception as e:
                    raise ExpressionError(
                        f"Failed to peek at queue path {self.path}: {e}",
                        expression=self,
                        cause=e,
                    )
        else:
            # Use transaction when storing the peeked value
            with self.app.state.tree.transaction() as transaction:
                view, path = self._resolve_path(
                    self.path, self.app.state.tree, transaction, context
                )
                queue_view = view.view(str(path), QueueView)

                # Peek at the value
                try:
                    peeked_value = queue_view.peek()
                except Exception as e:
                    raise ExpressionError(
                        f"Failed to peek at queue path {self.path}: {e}",
                        expression=self,
                        cause=e,
                    )

                # Store the peeked value
                store_view, store_path = self._resolve_path(
                    self.store_at, self.app.state.tree, transaction, context
                )
                try:
                    store_view.set(store_path, peeked_value)  # type: ignore
                except Exception as e:
                    raise ExpressionError(
                        f"Failed to store peeked value at path {self.store_at}: {e}",
                        expression=self,
                        cause=e,
                    )


class ClearQueue(Expression[SyncAppProtocol]):
    """
    Remove all items from a queue.

    This expression removes all items from the specified queue, leaving it empty.
    The operation is atomic - either all items are removed or none are.

    Args:
        path: State path to the queue (e.g., ("work_queue",) or ("tasks", "pending"))

    Examples:
        ```python
        # Clear a work queue
        ClearQueue(self, ("work_queue",))

        # Clear nested queue path
        ClearQueue(self, ("tasks", "failed"))

        # Clear notification queue
        ClearQueue(self, ("notifications", "pending"))
        ```
    """

    def __init__(self, app, path: ExpressionPath, **kwargs):
        super().__init__(app, **kwargs)
        self.path = path

    def do_evaluate(self, context: "Context") -> None:
        """Remove all items from the queue."""
        with self.app.state.tree.transaction() as transaction:
            # Get queue view at the specified path
            view, path = self._resolve_path(self.path, self.app.state.tree, transaction, context)
            queue_view = view.view(str(path), QueueView)

            # Clear all items from the queue
            try:
                queue_view.clear()
            except Exception as e:
                raise ExpressionError(
                    f"Failed to clear queue at path {self.path}: {e}",
                    expression=self,
                    cause=e,
                )


class OnQueueChange(Expression[SyncAppProtocol]):
    """
    Block and wait for queue changes, then execute expression sequentially.

    This blocking reactive expression waits for changes at the specified queue path,
    executes the provided expression once when a change occurs, then waits for the
    next change. This creates a sequential, blocking loop that processes queue changes
    one at a time.

    The expression blocks indefinitely, processing changes as they occur. Each change
    triggers exactly one execution of the provided expression, and the next change
    is only processed after the current expression completes.

    Args:
        path: State path to the queue to monitor (e.g., ("work_queue",) or ("tasks", "pending"))
        expression: Expression to execute when queue changes (executed sequentially)
        depth: Subscription depth (default 1 to monitor immediate queue changes)

    Examples:
        ```python
        # Block and process each queue change sequentially
        OnQueueChange(
            self,
            ("work_queue",),
            Sequence(
                self,
                Print(self, "Processing queue change..."),
                Dequeue(self, ("work_queue",), store_at=("current_task",)),
                Print(self, Path().current_task, message="Processing: {value}"),
                # ... process task ...
                Print(self, "Task completed, waiting for next change...")
            )
        )

        # Monitor high-priority queue with detailed logging
        OnQueueChange(
            self,
            ("tasks", "priority", "high"),
            Sequence(
                self,
                Print(self, "🚨 High priority task detected!"),
                Peek(self, ("tasks", "priority", "high"), store_at=("temp", "next_task")),
                Print(self, Path().temp.next_task, message="Next high priority: {value}"),
                # Process immediately...
            ),
            depth=0  # Monitor exact path only
        )
        ```

    Note:
        This expression blocks indefinitely in a loop. It will only terminate if:
        1. The provided expression raises an unhandled exception
        2. The application is shut down
        3. The subscription fails

        Each queue change triggers exactly one execution of the expression.
        The next change is only processed after the current execution completes.
    """

    def __init__(
        self,
        app,
        path: ExpressionPath,
        expression: Expression,
        *,
        stop_when: ExpressionValue | None = None,
        depth: int = 1,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.path = path
        self.expression = expression
        self.depth = depth
        self.stop_when = stop_when

    def do_evaluate(self, context: "Context") -> None:
        """Block and wait for queue changes, executing expression sequentially."""
        try:
            # Event to signal when a change occurs
            change_event = threading.Event()

            # Create callback function that signals change events
            def on_queue_change_callback(changed_path_tuple):
                """Signal that a queue change occurred."""
                change_event.set()

            queue_path = None
            # Convert path to tuple format for backend subscription
            with self.app.state.tree.snapshot() as snapshot:
                view, path = self._resolve_path(self.path, self.app.state.tree, snapshot, context)
                queue_view = view.view(str(path), QueueView)
                queue_path = queue_view.path

            # Subscribe to changes at the queue path
            subscription = self.app.state.tree.at(*queue_path.components).subscribe(
                callback=on_queue_change_callback, depth=self.depth
            )

            try:
                # Blocking loop: wait for changes and process them sequentially
                while True:
                    # Block until a queue change occurs
                    change_event.wait()

                    # Clear the event for the next iteration
                    change_event.clear()

                    # Execute the provided expression
                    try:
                        self.expression.evaluate(context)
                    except Exception as expression_error:
                        raise expression_error

                    # After expression completes, loop back to wait for next change
                    # (change_event.wait() will block until the next change occurs)

                    # Check stop condition after expression completes
                    if self.stop_when is not None:
                        with self.app.state.tree.snapshot() as snapshot:
                            stop_value = self._resolve_value(
                                self.stop_when, self.app.state.tree, snapshot, context
                            )
                            if stop_value:  # Break if condition is truthy
                                break
            finally:
                # Clean up subscription
                try:
                    self.app.state.tree.unsubscribe(subscription)
                except Exception as cleanup_error:
                    print(f"Error cleaning up OnQueueChange subscription: {cleanup_error}")

        except Exception as e:
            raise ExpressionError(
                f"Failed to set up blocking queue change monitoring for path {self.path}: {e}",
                expression=self,
                cause=e,
            )
