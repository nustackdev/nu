"""
Priority-based task processor using Loomi.

This example demonstrates how to implement a priority-based task processing system
with appropriate concurrency controls and handling of dynamically added high-priority tasks.
"""

from __future__ import annotations

import asyncio
import random
import time
from pathlib import Path
from typing import cast

# Loomi imports
from loomi import AsyncApp, Context, Operation, Spec
from loomix.logging import setup_logging

# Setup logging
setup_logging(Path(".logs"), log_level=10)


class PriorityTaskApp(AsyncApp):
    """Application demonstrating priority-based task processing."""

    # --- Task Methods (perform actions) ---

    async def init_state(self, context: Context):
        """Initialize state with task queues and sample tasks."""
        print(f"[{time.strftime('%H:%M:%S')}] Initializing state with task queues")

        # Create priority queues
        high_priority = {
            "task1": {"description": "Critical system update", "estimated_time": 2.0},
            "task2": {"description": "Security alert", "estimated_time": 1.5},
        }

        medium_priority = {
            "task3": {"description": "Database maintenance", "estimated_time": 3.0},
            "task4": {"description": "User report processing", "estimated_time": 2.5},
            "task5": {"description": "Analytics job", "estimated_time": 2.0},
        }

        low_priority = {
            "task6": {"description": "Cleanup old logs", "estimated_time": 1.0},
            "task7": {"description": "Update documentation", "estimated_time": 1.5},
            "task8": {"description": "Optimize database indexes", "estimated_time": 3.5},
        }

        # Store in state
        context.scope.dict("tasks").set("high_priority", value=high_priority)
        context.scope.dict("tasks").set("medium_priority", value=medium_priority)
        context.scope.dict("tasks").set("low_priority", value=low_priority)

        # Initialize results collection
        context.scope.dict("results")

        # Initialize metrics
        context.scope.dict("metrics").set(
            "processed_count", value={"high": 0, "medium": 0, "low": 0}
        )
        context.scope.dict("metrics").set("total_time", value={"high": 0, "medium": 0, "low": 0})

        print(
            f"[{time.strftime('%H:%M:%S')}] State initialized with {len(high_priority)} high, {len(medium_priority)} medium, and {len(low_priority)} low priority tasks"
        )

    async def add_high_priority_task(self, context: Context):
        """Simulate a new high-priority task arriving during processing."""
        await asyncio.sleep(3.0)  # Wait a bit before adding the task

        high_priority = context.scope.dict("tasks", "high_priority")
        new_task_id = f"task{random.randint(100, 999)}"

        print(f"[{time.strftime('%H:%M:%S')}] 🔴 ADDING NEW HIGH-PRIORITY TASK: {new_task_id}")

        high_priority.set(
            new_task_id,
            value={
                "description": "Emergency security patch",
                "estimated_time": 1.0,
            },
        )

    async def process_high_priority_task(self, context: Context):
        """Process a high-priority task."""
        task_id = context["map_key"]
        task_dict = context.scope.dict("tasks", "high_priority")
        task = cast(dict, task_dict.get(task_id))

        print(
            f"[{time.strftime('%H:%M:%S')}] Processing HIGH priority task: {task_id} - {task['description']}"
        )

        try:
            estimated_time = task["estimated_time"]
            execution_time = estimated_time * (0.8 + 0.4 * random.random())

            # Occasionally fail tasks to demonstrate retry behavior
            if random.random() < 0.3:  # 30% chance of failure
                print(
                    f"[{time.strftime('%H:%M:%S')}] ❌ Task {task_id} failing (will retry if allowed)"
                )
                await asyncio.sleep(execution_time / 3)  # Partial execution before failure
                raise RuntimeError(f"Simulated failure in task {task_id}")

            await asyncio.sleep(execution_time)

            # Mark the task as processed
            task["processed"] = True
            task["processed_at"] = time.strftime("%H:%M:%S")
            task["execution_time"] = execution_time

            # Update metrics
            metrics = context.scope.dict("metrics")
            processed_count = cast(dict, metrics.get("processed_count"))
            processed_count["high"] += 1
            metrics.set("processed_count", value=processed_count)

            total_time = cast(dict, metrics.get("total_time"))
            total_time["high"] += execution_time
            metrics.set("total_time", value=total_time)

            print(
                f"[{time.strftime('%H:%M:%S')}] ✅ Completed HIGH priority task: {task_id} in {execution_time:.2f}s"
            )

            # Move to results
            results = context.scope.dict("results")
            results.set(
                task_id,
                value={
                    **task,
                    "priority_level": "high_priority",
                },
            )

            # Remove from priority queue
            task_dict.delete(task_id)

            print(f"[{time.strftime('%H:%M:%S')}] ➡️ Moved completed task {task_id} to results")

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Error processing task {task_id}: {str(e)}")
            raise

    async def process_medium_priority_task(self, context: Context):
        """Process a medium-priority task."""
        task_id = context["map_key"]
        task_dict = context.scope.dict("tasks", "medium_priority")
        task = cast(dict, task_dict.get(task_id))

        print(
            f"[{time.strftime('%H:%M:%S')}] Processing MEDIUM priority task: {task_id} - {task['description']}"
        )

        try:
            estimated_time = task["estimated_time"]
            execution_time = estimated_time * (0.8 + 0.4 * random.random())

            # Occasionally fail tasks to demonstrate retry behavior
            if random.random() < 0.3:  # 30% chance of failure
                print(
                    f"[{time.strftime('%H:%M:%S')}] ❌ Task {task_id} failing (will retry if allowed)"
                )
                await asyncio.sleep(execution_time / 3)  # Partial execution before failure
                raise RuntimeError(f"Simulated failure in task {task_id}")

            await asyncio.sleep(execution_time)

            # Mark the task as processed
            task["processed"] = True
            task["processed_at"] = time.strftime("%H:%M:%S")
            task["execution_time"] = execution_time

            # Update metrics
            metrics = context.scope.dict("metrics")
            processed_count = cast(dict, metrics.get("processed_count"))
            processed_count["medium"] += 1
            metrics.set("processed_count", value=processed_count)

            total_time = cast(dict, metrics.get("total_time"))
            total_time["medium"] += execution_time
            metrics.set("total_time", value=total_time)

            print(
                f"[{time.strftime('%H:%M:%S')}] ✅ Completed MEDIUM priority task: {task_id} in {execution_time:.2f}s"
            )

            # Move to results
            results = context.scope.dict("results")
            results.set(
                task_id,
                value={
                    **task,
                    "priority_level": "medium_priority",
                },
            )

            # Remove from priority queue
            task_dict.delete(task_id)

            print(f"[{time.strftime('%H:%M:%S')}] ➡️ Moved completed task {task_id} to results")

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Error processing task {task_id}: {str(e)}")
            raise

    async def process_low_priority_task(self, context: Context):
        """Process a low-priority task."""
        task_id = context["map_key"]
        task_dict = context.scope.dict("tasks", "low_priority")
        task = cast(dict, task_dict.get(task_id))

        print(
            f"[{time.strftime('%H:%M:%S')}] Processing LOW priority task: {task_id} - {task['description']}"
        )

        try:
            estimated_time = task["estimated_time"]
            execution_time = estimated_time * (0.8 + 0.4 * random.random())

            # Occasionally fail tasks to demonstrate retry behavior
            if random.random() < 0.3:  # 30% chance of failure
                print(
                    f"[{time.strftime('%H:%M:%S')}] ❌ Task {task_id} failing (will retry if allowed)"
                )
                await asyncio.sleep(execution_time / 3)  # Partial execution before failure
                raise RuntimeError(f"Simulated failure in task {task_id}")

            await asyncio.sleep(execution_time)

            # Mark the task as processed
            task["processed"] = True
            task["processed_at"] = time.strftime("%H:%M:%S")
            task["execution_time"] = execution_time

            # Update metrics
            metrics = context.scope.dict("metrics")
            processed_count = cast(dict, metrics.get("processed_count"))
            processed_count["low"] += 1
            metrics.set("processed_count", value=processed_count)

            total_time = cast(dict, metrics.get("total_time"))
            total_time["low"] += execution_time
            metrics.set("total_time", value=total_time)

            print(
                f"[{time.strftime('%H:%M:%S')}] ✅ Completed LOW priority task: {task_id} in {execution_time:.2f}s"
            )

            # Move to results
            results = context.scope.dict("results")
            results.set(
                task_id,
                value={
                    **task,
                    "priority_level": "low_priority",
                },
            )

            # Remove from priority queue
            task_dict.delete(task_id)

            print(f"[{time.strftime('%H:%M:%S')}] ➡️ Moved completed task {task_id} to results")

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Error processing task {task_id}: {str(e)}")
            raise

    async def generate_summary(self, context: Context):
        """Generate a summary of all processed tasks."""
        results = context.scope.dict("results")
        results_items = results.items()

        metrics = cast(dict, context.scope.dict("metrics"))
        processed_count = cast(dict, metrics.get("processed_count"))
        total_time = cast(dict, metrics.get("total_time"))

        print("\n" + "=" * 50)
        print(f"PROCESSING SUMMARY ({len(results_items)} tasks completed)")
        print("=" * 50)

        # Print by priority level
        for priority in ["high", "medium", "low"]:
            priority_tasks = [
                item
                for item in results_items
                if item[1]["priority_level"] == f"{priority}_priority"
            ]
            avg_time = (
                total_time[priority] / processed_count[priority]
                if processed_count[priority] > 0
                else 0
            )

            print(f"\n{priority.upper()} PRIORITY:")
            print(f"  • Tasks completed: {processed_count[priority]}")
            print(f"  • Total processing time: {total_time[priority]:.2f}s")
            print(f"  • Average processing time: {avg_time:.2f}s")

            for task_id, task in sorted(priority_tasks):
                print(f"  • {task_id}: {task['description']} - {task['execution_time']:.2f}s")

        print("\n" + "=" * 50 + "\n")

    # --- Branch condition functions ---

    async def has_high_priority_tasks(self, context: Context) -> bool:
        """Check if there are any high-priority tasks to process."""
        high_priority = context.scope.dict("tasks", "high_priority")
        high_priority_keys = high_priority.keys()

        if high_priority_keys:
            print(
                f"[{time.strftime('%H:%M:%S')}] 🔴 Found {len(high_priority_keys)} high priority tasks"
            )
            return True
        return False

    async def has_medium_priority_tasks(self, context: Context) -> bool:
        """Check if there are any medium-priority tasks to process."""
        medium_priority = context.scope.dict("tasks", "medium_priority")
        medium_priority_keys = medium_priority.keys()

        if medium_priority_keys:
            print(
                f"[{time.strftime('%H:%M:%S')}] 🟠 Found {len(medium_priority_keys)} medium priority tasks"
            )
            return True
        return False

    async def has_low_priority_tasks(self, context: Context) -> bool:
        """Check if there are any low-priority tasks to process."""
        low_priority = context.scope.dict("tasks", "low_priority")
        low_priority_keys = low_priority.keys()

        if low_priority_keys:
            print(
                f"[{time.strftime('%H:%M:%S')}] 🟢 Found {len(low_priority_keys)} low priority tasks"
            )
            return True
        return False

    async def queue_decision(self, context: Context) -> str:
        """Determine which priority queue to process next."""
        # Check priorities in order
        if await self.has_high_priority_tasks(context):
            return "high"
        if await self.has_medium_priority_tasks(context):
            return "medium"
        if await self.has_low_priority_tasks(context):
            return "low"
        return "none"  # No tasks in any queue

    async def should_continue_processing(self, context: Context) -> bool:
        """Determine whether to continue the processing loop."""
        decision = await self.queue_decision(context)
        has_tasks = decision != "none"

        if not has_tasks:
            print(f"[{time.strftime('%H:%M:%S')}] All task queues are empty, processing complete")

        return has_tasks

    # --- Operation Definition Methods (define operation graphs) ---

    def process_high_priority_tasks(self) -> Operation:
        """Define operations for processing high-priority tasks."""
        return self.ex.Map(
            self.ex.Retry(
                self.ex.Function(self.process_high_priority_task),
                max_attempts=3,  # More retries for high-priority tasks
                backoff_factor=1.5,
                initial_delay=0.5,
            ),
            items_path=("_", "tasks", "high_priority"),
            max_concurrency=3,  # Process more high-priority tasks simultaneously
            error_behavior="fail",  # Continue on error for high-priority tasks
            on_fail=self.ex.Function(
                lambda context: print(
                    f"[{time.strftime('%H:%M:%S')}] ❌ High-priority task failed: {context['map_key']}"
                )
            ),
        )

    def process_medium_priority_tasks(self) -> Operation:
        """Define operations for processing medium-priority tasks."""
        return self.ex.Map(
            self.ex.Retry(
                self.ex.Function(self.process_medium_priority_task),
                max_attempts=2,  # Moderate number of retries
                backoff_factor=1.5,
                initial_delay=1.0,
            ),
            items_path=("_", "tasks", "medium_priority"),
            max_concurrency=2,  # Moderate concurrency
            error_behavior="continue",  # Continue on error for low-priority tasks
        )

    def process_low_priority_tasks(self) -> Operation:
        """Define operations for processing low-priority tasks."""
        return self.ex.Map(
            self.ex.Retry(
                self.ex.Function(self.process_low_priority_task),
                max_attempts=1,  # Minimal retries for low-priority tasks
                backoff_factor=1.0,
                initial_delay=1.0,
            ),
            items_path=("_", "tasks", "low_priority"),
            max_concurrency=1,  # Process low-priority tasks one at a time
            error_behavior="continue",  # Continue on error for low-priority tasks
        )

    def process_next_priority_level(self) -> Operation:
        """Define operations for processing the next priority level based on the queue decision."""
        return self.ex.Branch(
            {
                "high": self.process_high_priority_tasks(),
                "medium": self.process_medium_priority_tasks(),
                "low": self.process_low_priority_tasks(),
                "none": self.ex.Function(lambda _: None),  # No-op if no tasks
            },
            condition=self.queue_decision,
        )

    def priority_processing_loop(self) -> Operation:
        """Define the main priority-based processing loop."""
        return self.ex.Loop(
            # Process the next highest priority level
            self.process_next_priority_level(),
            condition=self.should_continue_processing,
        )

    def define(self) -> Operation:
        """Define the main workflow for priority-based task processing."""
        return self.ex.Sequence(
            # Initialize state
            self.ex.Function(self.init_state),
            # Set up parallel operations
            self.ex.Parallel(
                # Process tasks in priority order
                self.priority_processing_loop(),
                # Simulate a new high-priority task arriving during processing
                self.ex.Function(self.add_high_priority_task),
            ),
            # Generate summary after all processing is complete
            self.ex.Function(self.generate_summary),
        )


async def main():
    """Run the priority task processing example."""

    # Basic configuration
    from loomistd.specs import AsyncExecutorSpec, SyncStateSpec

    state_spec = SyncStateSpec().with_value_at("storage_srv", "path", value=".db")
    executor_spec = AsyncExecutorSpec(state=state_spec).with_value_at(
        "tracing", "state", "storage_srv", "path", value=".tracing"
    )

    # Create and run the application
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting priority-based task processing example\n")

    async with PriorityTaskApp(
        Spec(factory=PriorityTaskApp),
        state_spec=state_spec,
        executor_spec=executor_spec,
    ) as app:
        # Start the app
        await app.start()

    print(f"\n[{time.strftime('%H:%M:%S')}] Priority-based task processing example completed\n")


if __name__ == "__main__":
    asyncio.run(main())
