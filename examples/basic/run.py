"""
Compact example demonstrating core Loomi operations.

This example creates a simple workflow that demonstrates:
- Atomic: Function
- Flow: Sequence, Branch
- Timing: Retry
- State: Using state to control workflow
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

# Loomi imports
from loomi import AsyncApp, Context, Operation, Spec
from loomistd.aexecutor import ExecutionEngineSpec
from loomistd.state import StateSpec
from loomix.logging import setup_logging

# Setup logging
setup_logging(Path(".logs"), log_level=10)

# Basic state configuration
state_spec = StateSpec()
executor_spec = ExecutionEngineSpec(state=state_spec)


class BasicApp(AsyncApp):
    """A simple app demonstrating basic Loomi operations."""

    # --- Basic tasks ---
    async def hello_world(self, context: Context):
        """Simple task that prints a hello message and sets state."""
        print(f"[{time.strftime('%H:%M:%S')}] Hello, Loomi world!")

        # Store path choice in state
        path_choice = "b"  # In a real app, this could be determined by business logic
        context.scope.set("path", value=path_choice)

        print(f"[{time.strftime('%H:%M:%S')}] Set path to '{path_choice}' in state")

    async def flaky_task(self, context: Context):
        """Task that sometimes fails, demonstrating retry functionality."""
        attempt = context["retry_attempt"] if "retry_attempt" in context else 0
        print(f"[{time.strftime('%H:%M:%S')}] Flaky task executing (attempt {attempt + 1})")

        # Fail on first attempt, succeed on second attempt
        if attempt == 0:
            await asyncio.sleep(0.5)
            print(f"[{time.strftime('%H:%M:%S')}] Flaky task failing on purpose")
            raise ConnectionError("Simulated error")
        else:
            await asyncio.sleep(0.5)
            print(f"[{time.strftime('%H:%M:%S')}] Flaky task succeeded on attempt {attempt + 1}")

    # --- Flow control functions ---
    async def branch_decision(self, context: Context):
        """Return a path based on state value."""
        # Get path from state using the "_" root
        result = context.scope.get("path")
        print(f"[{time.strftime('%H:%M:%S')}] Branch decision from state: taking path {result}")
        return result

    # --- Branch path functions ---
    async def path_a_task(self, context: Context):
        """Execute when branch takes path A."""
        print(f"[{time.strftime('%H:%M:%S')}] PATH A task executing")
        await asyncio.sleep(0.5)
        print(f"[{time.strftime('%H:%M:%S')}] PATH A task completed")

    async def path_b_task(self, context: Context):
        """Execute when branch takes path B."""
        print(f"[{time.strftime('%H:%M:%S')}] PATH B task executing")
        await asyncio.sleep(0.5)
        print(f"[{time.strftime('%H:%M:%S')}] PATH B task completed")

    def define(self) -> Operation:
        """Define the workflow for this app."""
        return self.ex.Sequence(
            # 1. Simple Function operation that also sets state
            self.ex.Function(self.hello_world),
            # 2. Retry operation - automatically retries on failure
            self.ex.Retry(
                self.ex.Function(self.flaky_task),
                max_attempts=3,
                backoff_factor=1.5,
                initial_delay=0.5,
            ),
            # 3. Branch operation - takes different paths based on state
            self.ex.Branch(
                {
                    "a": self.ex.Function(self.path_a_task),
                    "b": self.ex.Function(self.path_b_task),
                    None: self.ex.Function(self.hello_world),  # Default path
                },
                condition=self.branch_decision,
            ),
        )


async def main():
    """Run the example."""
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting compact Loomi example\n")

    # Initialize state with a default value for path B
    # This demonstrates that we can pre-populate state before the workflow runs
    # The hello_world function will override this with path A
    initial_state = {"path": "b"}

    # Create and run the application
    async with BasicApp(
        Spec(factory=BasicApp),
        state_spec=state_spec,
        executor_spec=executor_spec,
    ) as app:
        # Initialize state
        app.state.dict("_").store(initial_state)
        print(f"[{time.strftime('%H:%M:%S')}] Initialized state with path 'b'")

        # Start the app (hello_world will change path to 'a')
        await app.start()

        # Read final state to verify
        final_path = app.state.dict("_").get("path")
        print(f"[{time.strftime('%H:%M:%S')}] Final path in state: {final_path}")

    print(f"\n[{time.strftime('%H:%M:%S')}] Compact Loomi example completed\n")


if __name__ == "__main__":
    asyncio.run(main())
