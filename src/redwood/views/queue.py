"""QueueView implementation for the tree storage.

This module defines the QueueView class, which provides a queue-like
interface for containers implementing the QUEUE structure with FIFO semantics.
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, cast

import attrs

from redwood.tree import BaseView, ContainerProtocol, ContainerStructure, TreeT
from redwood.tree.registry import ComponentConstructor, ContainerConstructor


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.types import Value

__all__ = [
    "QueueComponent",
    "QueueContainer",
    "QueueView",
]


@attrs.define(frozen=True, kw_only=True)
class QueueView(BaseView[TreeT]):
    """Queue view for containers implementing the QUEUE structure.

    QueueView provides a queue-like interface for interacting with
    containers, allowing FIFO (First In, First Out) operations.
    It supports standard queue operations like enqueue, dequeue, peek,
    with all data stored persistently using timestamp-based keys.

    The QueueView uses timestamp + UUID keys for ordering and uniqueness,
    ensuring distributed safety and maintaining FIFO semantics across
    multiple processes without requiring any metadata storage.

    Example:
        ```python
        # Create a queue view
        work_queue = tree.at("tasks").queue_view()

        # Enqueue values
        work_queue.enqueue("process_order_123")
        work_queue.enqueue({"task": "send_email", "priority": "high"})

        # Check queue state
        if not work_queue.is_empty():
            next_task = work_queue.peek()  # Look at front without removing
            current_task = work_queue.dequeue()  # Remove and return front item

        # Check size
        print(f"Queue size: {work_queue.size()}")

        # Bulk operations
        tasks = ["task1", "task2", "task3"]
        work_queue.store(tasks)  # Add all tasks to queue

        # Convert to list (maintains FIFO order)
        all_tasks = work_queue.extract()

        # Clear all items
        work_queue.clear()
        ```
    """

    structure: ContainerStructure = attrs.field(default=ContainerStructure(101), init=False)

    protocol: ContainerProtocol = attrs.field(default=ContainerProtocol.MUTABLE, init=False)

    def _generate_key(self) -> str:
        """Generate a unique timestamp-based key for queue ordering.

        Uses Unix nanosecond timestamp + UUID for global uniqueness and ordering.
        Keys naturally sort in FIFO order due to timestamp prefix.

        Returns:
            str: Unique key in format "{timestamp_ns}_{uuid8}"

        Example:
            "1704067200123456789_a1b2c3d4"
        """
        timestamp = time.time_ns()  # Unix nanoseconds since epoch
        unique_id = uuid.uuid4().hex[:8]  # 8-char UUID for deduplication
        return f"{timestamp}_{unique_id}"

    def extract(self) -> list[Value]:
        """Extract all queue contents as a list in FIFO order.

        Returns:
            list[Value]: All queue items from front to back

        Example:
            ```python
            queue_contents = work_queue.extract()
            # Returns: [front_item, ..., back_item]
            ```
        """
        return [cast("Value", self._get_child_value(key)) for key in self.container.keys()]

    def store(self, values, /, *, replace: bool = False) -> None:
        """Store iterable values in the queue.

        Args:
            values: Iterable of values to enqueue
            replace: If True, clears existing queue first. If False, appends to existing queue.

        Raises:
            TypeError: If values is not iterable or is string/bytes/dict

        Example:
            ```python
            # Append to existing queue
            work_queue.store(["task1", "task2", "task3"])

            # Replace entire queue
            work_queue.store(["new_task1", "new_task2"], replace=True)
            ```
        """
        # If replacing, clear existing items
        if replace:
            self.clear()

        # Enqueue each item
        for item in values:
            self.enqueue(item)

    def enqueue(self, value: Value) -> None:
        """Add value to the back of the queue.

        Args:
            value: Value to add to queue

        Example:
            ```python
            work_queue.enqueue("process_order")
            work_queue.enqueue({"task": "send_notification", "user_id": 123})
            ```
        """
        key = self._generate_key()
        self._set_child_value(key, value)

    def dequeue(self) -> Value:
        """Remove and return the front item from the queue.

        Returns:
            Value: The front item that was removed

        Raises:
            IndexError: If queue is empty

        Example:
            ```python
            try:
                next_task = work_queue.dequeue()
                process_task(next_task)
            except IndexError:
                print("Queue is empty")
            ```
        """
        keys_iter = self.container.keys()
        try:
            front_key = next(keys_iter)  # First key is front of queue (lexicographically smallest)
        except StopIteration:
            raise IndexError("dequeue from empty queue")

        value = self._get_child_value(front_key)
        self.container.remove_child(front_key)
        return cast("Value", value)

    def peek(self) -> Value:
        """Look at the front item without removing it.

        Returns:
            Value: The front item (not removed)

        Raises:
            IndexError: If queue is empty

        Example:
            ```python
            if not work_queue.is_empty():
                next_task = work_queue.peek()
                print(f"Next task: {next_task}")
            ```
        """
        keys_iter = self.container.keys()
        try:
            front_key = next(keys_iter)  # First key is front of queue (lexicographically smallest)
        except StopIteration:
            raise IndexError("peek from empty queue")

        return cast("Value", self._get_child_value(front_key))

    def is_empty(self) -> bool:
        """Check if the queue has no items.

        Returns:
            bool: True if queue is empty, False otherwise

        Example:
            ```python
            if work_queue.is_empty():
                print("No tasks to process")
            else:
                task = work_queue.dequeue()
            ```
        """
        # Check if any keys exist
        try:
            next(self.container.keys())
            return False
        except StopIteration:
            return True

    def size(self) -> int:
        """Get the number of items in the queue.

        Returns:
            int: Number of items in the queue

        Example:
            ```python
            queue_size = work_queue.size()
            print(f"Processing {queue_size} tasks")
            ```
        """
        return sum(1 for _ in self.container.keys())

    def clear(self) -> int:
        """Remove all items from the queue.

        Returns:
            int: Number of items that were removed

        Example:
            ```python
            removed_count = work_queue.clear()
            print(f"Cleared {removed_count} tasks")
            ```
        """
        return self.container.clear_children()

    def values(self) -> Generator[Value, None, None]:
        """Get all values in the queue in FIFO order.

        Yields:
            Value: Queue values from front to back

        Example:
            ```python
            for task in work_queue.values():
                print(f"Queued task: {task}")
            ```
        """
        for key in self.container.keys():
            yield cast("Value", self._get_child_value(key))


class QueueContainer(ContainerConstructor):
    pass


class QueueComponent(ComponentConstructor):
    pass
