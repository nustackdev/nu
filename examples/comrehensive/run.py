"""
Comprehensive example demonstrating the use of all implemented operations.

This example creates a workflow that combines all operations:
- Atomic: Function, App
- Flow: Sequence, Parallel, Branch, Loop
- Timing: Delay, Timeout, Retry
- Collection: Map
"""

from __future__ import annotations

import asyncio
import random
import time
from pathlib import Path

# Loomi
from loomi import AsyncApp, AsyncContext, AsyncOperation, Spec, UseApp
from loomi._logging import setup_logging
from loomistd.aexecutor import ExecutionEngineSpec
from loomistd.state import StateSpec

setup_logging(Path(".logs"), log_level=10)

state_spec = StateSpec()
executor_spec = ExecutionEngineSpec(state=state_spec)


class NestedApp(AsyncApp):
    """A simple nested app that will be executed by the main app."""

    async def greet(self, context: AsyncContext):
        """Greet the user."""
        print(f"[{time.strftime('%H:%M:%S')}] NestedApp: Hello from the nested app!")
        await asyncio.sleep(0.3)
        print(f"[{time.strftime('%H:%M:%S')}] NestedApp: Setting greeting in state")
        await context.scope.store("Hello from nested app!", "greeting")

    def define(self) -> AsyncOperation:
        """Define the nested app workflow."""
        return self.ex.Function(self.greet)


class ComprehensiveApp(AsyncApp):
    """Main application demonstrating all operation types."""

    nested_app = UseApp(NestedApp)

    # --- Basic tasks ---

    async def simple_task(self, context: AsyncContext):
        """Simple task that just logs a message."""
        print(f"[{time.strftime('%H:%M:%S')}] Simple task executing")
        await asyncio.sleep(0.3)
        print(f"[{time.strftime('%H:%M:%S')}] Simple task completed")

    async def delayed_task(self, context: AsyncContext):
        """Task to run after a delay."""
        print(f"[{time.strftime('%H:%M:%S')}] Delayed task executing")
        await asyncio.sleep(0.3)
        print(f"[{time.strftime('%H:%M:%S')}] Delayed task completed")

    async def long_running_task(self, context: AsyncContext):
        """Task that takes a long time to complete."""
        print(f"[{time.strftime('%H:%M:%S')}] Long-running task started (taking 3 seconds)")
        try:
            await asyncio.sleep(3.0)
            print(f"[{time.strftime('%H:%M:%S')}] Long-running task completed")
        except asyncio.CancelledError:
            print(f"[{time.strftime('%H:%M:%S')}] Long-running task was cancelled")
            raise

    async def unreliable_task(self, context: AsyncContext):
        """Task that sometimes fails, good for demonstrating retry."""
        attempt = context["retry_attempt"] if "retry_attempt" in context else 0

        print(f"[{time.strftime('%H:%M:%S')}] Unreliable task executing (attempt {attempt + 1})")

        # Fail on first attempt, succeed on subsequent attempts
        if attempt == 0:
            await asyncio.sleep(0.3)
            print(f"[{time.strftime('%H:%M:%S')}] Unreliable task failing on purpose")
            raise ConnectionError("Simulated connection error")
        else:
            await asyncio.sleep(0.3)
            print(
                f"[{time.strftime('%H:%M:%S')}] Unreliable task succeeded on attempt {attempt + 1}"
            )

    # --- Collection task ---

    async def process_item(self, context: AsyncContext):
        """Process a single item from a collection."""
        # Get item key and index from context
        item_key = context["map_key"] if "map_key" in context else "unknown_key"
        item_index = context["map_index"] if "map_index" in context else -1

        print(f"[{time.strftime('%H:%M:%S')}] Processing item {item_index}: {item_key}")

        # Get the item data
        item_value = await context.scope.get("value")

        # Simulate work
        duration = random.uniform(0.2, 0.8)
        await asyncio.sleep(duration)

        # Update the item
        await context.scope.set("processed", value=True)
        await context.scope.set("process_time", value=duration)

        print(
            f"[{time.strftime('%H:%M:%S')}] Completed processing item {item_key} ({item_value}) in {duration:.2f}s"
        )

    # --- Flow control functions ---

    async def branch_condition(self, context: AsyncContext):
        """Return a value to determine which branch to take."""
        choices = ["path1", "path2", "path3"]
        result = random.choice(choices)
        print(f"[{time.strftime('%H:%M:%S')}] Branch condition returning: {result}")
        return result

    async def loop_condition(self, context: AsyncContext):
        """Return whether to continue the loop."""
        iteration = context["iteration"] if "iteration" in context else random.randint(0, 4)
        should_continue = iteration < 2  # Will run 3 times (0, 1, 2)
        print(
            f"[{time.strftime('%H:%M:%S')}] Loop condition: continue={should_continue} (iteration={iteration})"
        )
        return should_continue

    # --- Handler functions ---

    async def timeout_handler(self, context: AsyncContext):
        """Handle timeout events."""
        print(f"[{time.strftime('%H:%M:%S')}] Timeout handler executing")
        await asyncio.sleep(0.2)
        print(f"[{time.strftime('%H:%M:%S')}] Timeout handler completed")

    async def error_handler(self, context: AsyncContext):
        """Handle errors in operations."""
        print(f"[{time.strftime('%H:%M:%S')}] Error handler executing")
        await asyncio.sleep(0.2)
        print(f"[{time.strftime('%H:%M:%S')}] Error handler completed")

    async def finalize(self, context: AsyncContext):
        """Run when a loop completes."""
        iterations = context["iterations_completed"] if "context" in context else 0
        print(
            f"[{time.strftime('%H:%M:%S')}] Finalize: Loop completed after {iterations} iterations"
        )

    # --- Branch path functions ---

    async def path1_task(self, context: AsyncContext):
        """Execute when branch takes path1."""
        print(f"[{time.strftime('%H:%M:%S')}] PATH 1 task executing")
        await asyncio.sleep(0.3)
        print(f"[{time.strftime('%H:%M:%S')}] PATH 1 task completed")

    async def path2_task(self, context: AsyncContext):
        """Execute when branch takes path2."""
        print(f"[{time.strftime('%H:%M:%S')}] PATH 2 task executing")
        await asyncio.sleep(0.3)
        print(f"[{time.strftime('%H:%M:%S')}] PATH 2 task completed")

    async def path3_task(self, context: AsyncContext):
        """Execute when branch takes path3."""
        print(f"[{time.strftime('%H:%M:%S')}] PATH 3 task executing")
        await asyncio.sleep(0.3)
        print(f"[{time.strftime('%H:%M:%S')}] PATH 3 task completed")

    # --- Setup and utilities ---

    async def setup_data(self, context: AsyncContext):
        """Set up test data for the workflow."""
        print(f"[{time.strftime('%H:%M:%S')}] Setting up test data")

        # Create a dictionary of items for Map operation
        items = {
            "item1": {"value": "First item"},
            "item2": {"value": "Second item"},
            "item3": {"value": "Third item"},
            "item4": {"value": "Fourth item"},
        }

        # Store in state
        await context.scope.store(items, "data", "items")

        print(f"[{time.strftime('%H:%M:%S')}] Test data setup completed")

    async def read_nested_app_result(self, context: AsyncContext):
        """Read the result from the nested app."""
        greeting = await context.scope.get("nested_app", "greeting")
        print(f"[{time.strftime('%H:%M:%S')}] Retrieved from nested app: {greeting}")

    def define(self) -> AsyncOperation:
        """Define the comprehensive workflow."""

        # Build a workflow demonstrating all operations
        workflow = self.ex.Sequence(
            # Setup phase
            self.ex.Function(self.setup_data),
            # 1. Simple Function operation
            self.ex.Function(self.simple_task),
            # 2. Delay operation - pauses execution for 1 second
            self.ex.Delay(1.0),
            self.ex.Function(self.delayed_task),
            # 3. App operation - runs a nested app
            self.ex.App(self.nested_app, state_path=("nested_app",)),
            self.ex.Function(self.read_nested_app_result),
            # 4. Timeout operation - runs with a time constraint
            self.ex.Timeout(
                self.ex.Function(self.long_running_task),
                timeout=1.5,  # Will timeout after 1.5 seconds
                on_timeout=self.ex.Function(self.timeout_handler),
                error_behavior="continue",  # Continue despite timeout
            ),
            # 5. Retry operation - retries unreliable tasks
            self.ex.Retry(
                self.ex.Function(self.unreliable_task),
                max_attempts=3,
                backoff_factor=2.0,
                initial_delay=0.5,
                max_delay=5.0,
            ),
            # 6. Parallel operation - runs multiple operations concurrently
            self.ex.Parallel(
                self.ex.Function(self.simple_task),
                self.ex.Function(self.delayed_task),
                self.ex.Function(self.simple_task),
                max_concurrency=2,  # Only run 2 at a time
            ),
            # 7. Branch operation - takes different paths based on a condition
            self.ex.Branch(
                {
                    "path1": self.ex.Function(self.path1_task),
                    "path2": self.ex.Function(self.path2_task),
                    "path3": self.ex.Function(self.path3_task),
                    None: self.ex.Function(self.simple_task),  # Default path
                },
                condition=self.branch_condition,
            ),
            # 8. Loop operation - repeats until condition is false
            self.ex.Loop(
                self.ex.Function(self.simple_task),
                condition=self.loop_condition,
                on_finish=self.ex.Function(self.finalize),
            ),
            # 9. Map operation - processes each item in a collection
            self.ex.Map(
                self.ex.Function(self.process_item),
                items_path=("_", "data", "items"),
                max_concurrency=2,  # Process up to 2 items concurrently
            ),
        )

        return workflow


class RunnerApp(AsyncApp):
    """Higher-order app that runs the ComprehensiveApp."""

    app1 = UseApp(ComprehensiveApp)

    def define(self) -> AsyncOperation:
        """Run the ComprehensiveApp."""
        return self.ex.App(self.app1)


async def main():
    """Run the example."""
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting comprehensive operations example\n")

    # Create and run the application
    async with RunnerApp(
        Spec(
            factory=RunnerApp,
            app1=Spec(  # type: ignore
                factory=ComprehensiveApp,
                nested_app=Spec(factory=NestedApp),  # type: ignore
            ),
        ),
        state_spec=state_spec,
        executor_spec=executor_spec,
    ) as app:
        # Render the operation tree
        # operation = app.define()

        # print("\nOperation Tree:")
        # app.eng.render(operation)
        # print("\nExecuting workflow:")

        # Start the app
        await app.start()

    print(f"\n[{time.strftime('%H:%M:%S')}] Comprehensive operations example completed\n")


if __name__ == "__main__":
    asyncio.run(main())
