"""
Example demonstrating the ReactiveMap operation.

This shows how ReactiveMap can be used to process items in a collection as they're added.
"""

from __future__ import annotations

import asyncio
import random
import time
from pathlib import Path

from loomi import AsyncApp, AsyncContext, AsyncOperation
from loomistd.aexecutor import ExecutionEngineSpec
from loomistd.aexecutor.services.tracing import TracingServiceSpec
from loomistd.compound_ops import ReactiveMap
from loomistd.kv_storage.file_storage import FileStorageSpec
from loomistd.state import StateSpec
from loomix.logging import setup_logging

# Basic setup
setup_logging(Path(".logs"), log_level=10)

# Configure service specs
state_spec = StateSpec()

tracing_state_spec = StateSpec(
    name="tracing_state", storage_srv=FileStorageSpec(path=Path(".tracing/db"))
)
executor_spec = ExecutionEngineSpec(
    state=state_spec,
    tracing=TracingServiceSpec(tracing_state=tracing_state_spec),
)


class TodoReactiveMapApp(AsyncApp):
    """App demonstrating ReactiveMap to process to-do items."""

    async def init_state(self, context: AsyncContext):
        """Initialize the state with an empty collection of todos."""
        await context.scope.dict("todos")
        print(f"[{time.strftime('%H:%M:%S')}] Initialized state with empty todos collection.")

    async def process_todo(self, context: AsyncContext):
        """Process a single to-do item."""

        # Get the to-do item from context
        change_path: tuple[str, ...] = (
            context["change_path"] if "change_path" in context else context["map_path"]
        )
        todo_dict = await self.state.dict(*change_path)

        title = await todo_dict.get("title", default="Untitled")
        priority = await todo_dict.get("priority", default="normal")

        print(f"[{time.strftime('%H:%M:%S')}] 🔄 PROCESSING: '{title}' (priority: {priority})")

        # Mark as processed
        await todo_dict.set("processed", value=True)
        await todo_dict.set("processed_at", value=time.strftime("%H:%M:%S"))

        # Simulate processing time
        await asyncio.sleep(0.5)

        print(f"[{time.strftime('%H:%M:%S')}] ✅ COMPLETED: '{title}'")

    async def add_random_todo(self, context: AsyncContext):
        """Add a new to-do item to the collection."""
        # Get todos collection
        todos = await context.scope.dict("todos")

        title = random.choice(
            [
                "Buy groceries",
                "Walk the dog",
                "Read a book",
                "Write code",
                "Clean the house",
            ]
        )
        priority = random.choice(["low", "medium", "high"])

        # Create a unique key (timestamp + title)
        key = f"{int(time.time())}-{title.replace(' ', '_')}"

        # Add the new item
        await todos.set(
            key,
            value={
                "title": title,
                "priority": priority,
                "created_at": time.strftime("%H:%M:%S"),
                "processed": False,
            },
        )

        print(f"[{time.strftime('%H:%M:%S')}] ➕ ADDED: '{title}' with key {key}")

    def define(self) -> AsyncOperation:
        return self.ex.Sequence(
            self.ex.Function(self.init_state),
            self.ex.Parallel(
                self.ex.Compound(ReactiveMap)(
                    self.ex.Function(self.process_todo),
                    items_path=("_", "todos"),
                    max_concurrency=2,
                ),
                self.ex.Sequence(
                    self.ex.Delay(1.0),
                    self.ex.Function(self.add_random_todo),
                    self.ex.Delay(1.5),
                    self.ex.Function(self.add_random_todo),
                    self.ex.Delay(2.0),
                    self.ex.Function(self.add_random_todo),
                    self.ex.Delay(2.5),
                    self.ex.Function(self.add_random_todo),
                    self.ex.Delay(3.0),
                ),
            ),
        )


async def main():
    """Run the ReactiveMap example."""
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting ReactiveMap Todo example\n")

    # Create and run the application
    async with TodoReactiveMapApp(
        state_spec=state_spec,
        executor_spec=executor_spec,
    ) as app:
        app.define()

        print("\nOperation Tree:")
        # app.eng.render(operation)
        print("\nExecuting workflow:")

        # Start the app
        await app.start()

    print(f"\n[{time.strftime('%H:%M:%S')}] Example completed\n")


if __name__ == "__main__":
    asyncio.run(main())
