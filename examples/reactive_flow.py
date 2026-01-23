"""Reactive Flow example - Once, OnChange, OnChangeWhile with subscriptions.

This example demonstrates:
1. Once - waiting for a single change before proceeding
2. OnChange - reacting to every change continuously
3. OnChangeWhile - reacting to changes while a condition holds

The example uses Parallel to simulate concurrent producers and consumers.
"""

import asyncio

from everyshape import Shape

from everybase.flow import (
    Delay,
    ForRange,
    Parallel,
    Print,
    React,
    ReactForever,
    ReactWhile,
    Sequence,
    Timeout,
)
from everybase.slot import (
    BoolSlot,
    DictSlot,
    IntSlot,
)


class TaskQueue(Shape):
    """A simple task queue with items and status."""

    aitems = DictSlot(str)  # task_id -> task_data
    is_active = BoolSlot()
    processed_count = IntSlot()


# =============================================================================
# Example 1: Once - Wait for first item, then process
# =============================================================================

once_example = Sequence(
    Print(message="[Once] Waiting for first task to be added..."),
    Parallel(
        # Consumer: wait for first task
        React(
            TaskQueue.aitems.on_children_change(),
            Sequence(
                Print(message="[Once] First task detected! Processing..."),
                Delay(0.1),
                Print(message="[Once] First task processed!"),
            ),
        ),
        # Producer: add a task after delay
        Sequence(
            Delay(0.5),
            Print(message="[Once] Adding first task..."),
            TaskQueue.aitems["task_1"].set("Do something important"),
        ),
    ),
    Print(message="[Once] Example complete!\n"),
)


# =============================================================================
# Example 2: OnChange - React to every change (with timeout to stop)
# =============================================================================

onchange_example = Sequence(
    Print(message="[OnChange] Starting continuous task processor..."),
    TaskQueue.processed_count.set(0),
    Timeout(
        timeout=3.0,  # Stop after 3 seconds
        child=Parallel(
            # Consumer: process every new task
            ReactForever(
                TaskQueue.aitems.on_children_change(),
                Sequence(
                    Print(message="[OnChange] Task change detected!"),
                    TaskQueue.processed_count.set(TaskQueue.processed_count.get() + 1),
                    Print(
                        message="[OnChange] Processed count:",
                        values=TaskQueue.processed_count.get(),
                    ),
                ),
            ),
            # Producer: add tasks periodically
            ForRange(
                start=1,
                stop=5,
                child=Sequence(
                    Delay(0.5),
                    Print(message="[OnChange] Adding new task..."),
                    # Use index to create unique task names
                    TaskQueue.aitems["task_new"].set("New task data"),
                ),
            ),
        ),
    ),
    Print(message="[OnChange] Example complete!\n"),
)


# =============================================================================
# Example 3: OnChangeWhile - React while condition is true
# =============================================================================

onchangewhile_example = Sequence(
    Print(message="[OnChangeWhile] Processing while queue is active..."),
    TaskQueue.is_active.set(True),
    TaskQueue.processed_count.set(0),
    Parallel(
        # Consumer: process while active
        ReactWhile(
            TaskQueue.aitems.on_children_change(),
            TaskQueue.is_active.get(),
            Sequence(
                Print(message="[OnChangeWhile] Processing task..."),
                TaskQueue.processed_count.set(TaskQueue.processed_count.get() + 1),
            ),
        ),
        # Producer: add tasks then deactivate
        Sequence(
            Delay(0.3),
            TaskQueue.aitems["w_task_1"].set("Task 1"),
            Delay(0.3),
            TaskQueue.aitems["w_task_2"].set("Task 2"),
            Delay(0.3),
            TaskQueue.aitems["w_task_3"].set("Task 3"),
            Delay(0.3),
            Print(message="[OnChangeWhile] Deactivating queue..."),
            TaskQueue.is_active.set(False),
            # This task should NOT be processed
            Delay(0.2),
            TaskQueue.aitems["w_task_4"].set("Task 4 - should not process"),
            Delay(0.5),
        ),
    ),
    Print(
        message="[OnChangeWhile] Final processed count:",
        values=TaskQueue.processed_count.get(),
    ),
    Print(message="[OnChangeWhile] Example complete!\n"),
)


# =============================================================================
# Example 4: OnPrimitiveChangeOp - Watch a single value
# =============================================================================

primitive_watch_example = Sequence(
    Print(message="[Primitive] Watching processed_count changes..."),
    TaskQueue.processed_count.set(0),
    Timeout(
        timeout=2.0,
        child=Parallel(
            # Consumer: watch the counter
            ReactForever(
                TaskQueue.processed_count.on_change(),
                Print(
                    message="[Primitive] Count changed to:",
                    values=TaskQueue.processed_count.get(),
                ),
            ),
            # Producer: increment counter
            ForRange(
                start=1,
                stop=4,
                child=Sequence(
                    Delay(0.4),
                    TaskQueue.processed_count.set(TaskQueue.processed_count.get() + 1),
                ),
            ),
        ),
    ),
    Print(message="[Primitive] Example complete!\n"),
)


# =============================================================================
# Main flow - run all examples
# =============================================================================

main_flow = Sequence(
    Print(message="=" * 60),
    Print(message="Reactive Flows Examples"),
    Print(message="=" * 60 + "\n"),
    once_example,
    Delay(0.5),
    onchange_example,
    Delay(0.5),
    onchangewhile_example,
    Delay(0.5),
    primitive_watch_example,
    Print(message="=" * 60),
    Print(message="All examples complete!"),
    Print(message="=" * 60),
)


async def main():
    from everybase.top import regular_provider, text_storage

    with text_storage(".db_reactive") as storage:
        await main_flow.start_flow(regular_provider(storage))


if __name__ == "__main__":
    asyncio.run(main())
