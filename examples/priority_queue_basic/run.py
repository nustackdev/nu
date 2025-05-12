"""
Priority-based task processor using Loomi.

This example demonstrates how to implement a simple priority-based task processing system
using Loomi. It initializes two queues: one for high-priority tasks and another for low-priority tasks.
Tasks are processed in order of priority, with high-priority tasks being processed first.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

# Loomi imports
from loomi import AsyncApp, Context, Operation, Spec
from loomistd.aexecutor import ExecutionEngineSpec
from loomistd.aexecutor.services.tracing import TracingServiceSpec
from loomistd.kv.file_storage import FileStorageSpec
from loomistd.state import StateSpec
from loomix.logging import setup_logging

# Setup logging
setup_logging(Path(".logs"), log_level=10)

# Basic state configuration
state_spec = StateSpec()
trasing_spec = TracingServiceSpec(
    tracing_state=StateSpec(storage_srv=FileStorageSpec(path=Path(".tracing/db")))
)
executor_spec = ExecutionEngineSpec(state=state_spec, tracing=trasing_spec)


class PriorityTaskApp(AsyncApp):
    """Demonstrates priority-based task processing with Loomi."""

    async def init_state(self, context: Context):
        """Initialize state with priority queues."""
        context.scope.set(
            "tasks",
            value={  # Initialize task storages with some dummy tasks
                "high_priority": {"task1": {"description": "Critical system update"}},
                "low_priority": {"task2": {"description": "Cleanup old logs"}},
            },
        )
        context.scope.set("results", value={})  # Initialize results storage

    async def process_high_priority_task(self, context: Context):
        """Process a high-priority task."""
        task_id = context["map_key"]
        print(f"Processing HIGH priority task: {task_id}")

        # Move task from high_priority queue to results
        context.scope.dict("tasks", "high_priority", task_id).move_to("_", "results", task_id)

    async def process_low_priority_task(self, context: Context):
        """Process a low-priority task."""
        task_id = context["map_key"]
        print(f"Processing LOW priority task: {task_id}")

        # Move task from low_priority queue to results
        context.scope.dict("tasks", "low_priority", task_id).move_to("_", "results", task_id)

    async def has_high_priority_tasks(self, context: Context) -> bool:
        """Check if high-priority tasks exist."""
        return bool(context.scope.dict("tasks", "high_priority").keys())

    async def has_tasks(self, context: Context) -> bool:
        """Check if high-priority tasks exist."""
        return bool(
            context.scope.dict("tasks", "high_priority").keys()
            or context.scope.dict("tasks", "low_priority").keys()
        )

    def define(self) -> Operation:
        """Define priority-based workflow processing."""
        return self.ex.Sequence(
            # Initialize priority queues
            self.ex.Function(self.init_state),
            # Loop through tasks until all are processed
            self.ex.Loop(
                # Process tasks in priority order
                self.ex.Branch(
                    {
                        # When high priority tasks exist, process those first
                        True: self.ex.Map(
                            self.ex.Function(self.process_high_priority_task),
                            items_path=("_", "tasks", "high_priority"),
                            max_concurrency=5,
                        ),
                        # Otherwise process low priority tasks
                        False: self.ex.Map(
                            self.ex.Function(self.process_low_priority_task),
                            items_path=("_", "tasks", "low_priority"),
                            max_concurrency=5,
                        ),
                    },
                    condition=self.has_high_priority_tasks,
                ),
                condition=self.has_tasks,
            ),
        )


async def main():
    """Run the priority task processing example."""
    print("\nStarting priority-based task processing example\n")

    # Create and run the application
    async with PriorityTaskApp(
        Spec(factory=PriorityTaskApp),
        state_spec=state_spec,
        executor_spec=executor_spec,
    ) as app:
        # Start the app
        await app.start()

    print("\nPriority-based task processing example completed\n")


if __name__ == "__main__":
    asyncio.run(main())
