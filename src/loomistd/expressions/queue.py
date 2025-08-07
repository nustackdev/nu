from __future__ import annotations

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
            queue_view.is_empty()  # Ensure the queue exists. TODO: Add init method or make this implicit

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
