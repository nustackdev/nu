"""
Loomi Operations Framework - Async Implementation

This package provides a framework for composing asynchronous workflows from
atomic operations. It follows a centralized execution model where operations
are defined as data structures and executed by a dedicated engine.

Core Components:
- Operations: Units of work that define workflow behavior
- ExecutionEngine: Central orchestrator for executing operations
- RuntimeContext: Execution context for operations
- Services: Cross-cutting capabilities (tracing, state, etc.)

Example usage:

```python
from loomi.app.lib.operations_async import (
    ExecutionBuilder,
    ExecutionEngine,
    Function,
)
from loomi.app.lib.state import AsyncState

# Create an execution engine
engine = ExecutionEngine()

# Register handlers for operation types
from loomi.app.lib.operations_async.core.function import handle_function_operation
engine.register_handler("function", handle_function_operation)

# Create a state provider
state = AsyncState()

# Define an operation
async def my_operation(context):
    await context.state.set(("greeting",), "Hello, world!")
    return "Operation completed"

op = Function(my_operation)

# Execute the operation
result = await ExecutionBuilder(engine, state).execute(op)
print(result)  # "Operation completed"
```
"""

# Core components
from .context import RuntimeContext

# Core operations
from .core.function import Function
from .engine import ExecutionBuilder, ExecutionEngine, ExecutionState, ExecutionStatus
from .errors import (
    OperationCancelledError,
    OperationConfigError,
    OperationError,
    OperationNotFoundError,
    OperationTimeoutError,
    StateAccessError,
)
from .operation import BaseOperation, ErrorBehavior, Operation, OperationMetadata
from .services import AsyncStateInterface, CancellationToken, ServiceRegistry, TracingService

__all__ = [
    # Core components
    "RuntimeContext",
    "ExecutionBuilder",
    "ExecutionEngine",
    "ExecutionState",
    "ExecutionStatus",
    # Errors
    "OperationError",
    "OperationTimeoutError",
    "OperationCancelledError",
    "StateAccessError",
    "OperationConfigError",
    "OperationNotFoundError",
    # Operation base
    "BaseOperation",
    "ErrorBehavior",
    "Operation",
    "OperationMetadata",
    # Services
    "AsyncStateInterface",
    "CancellationToken",
    "TracingService",
    "ServiceRegistry",
    # Core operations
    "Function",
]
