# Loomi Operations 

## 1. Mental Model & Core Principles

The Operations Library provides a consistent framework for composing asynchronous workflows from atomic operations. The mental model is built around these core principles:

### 1.1 Core Principles

- **Composability**: Operations can be nested and combined to build complex workflows from simple parts
- **Consistency**: All operations follow the same patterns for initialization, execution, error handling, and state management
- **Predictability**: Operations behave in consistent ways when faced with similar circumstances (errors, cancellation, etc.)
- **Explicitness**: The intent of operations is clear from their interfaces and names
- **Developer Experience**: Prioritize intuitive APIs, helpful error messages, and easy debugging

### 1.2 Mental Model

The library is built around a clear mental model:

1. **Operations as First-Class Objects**: Each operation is an encapsulated unit of behavior that:
    - Executes asynchronously
    - Has access to shared state through a standardized interface
    - May interact with other operations in defined ways
    - Has a clear beginning and end (with specific exceptions for reactive operations)
2. **Workflow as Composition**: Complex workflows are built by composing operations through:
    - Sequential execution (one operation after another)
    - Parallel execution (multiple operations concurrently)
    - Conditional execution (operations that may or may not run based on conditions)
    - etc
3. **Shared State Model**: All operations interact with state through a consistent interface that:
    - Provides structured access to the application's state
    - Ensures isolation between different parts of the state
    - Allows for reactive updates and subscriptions

## 2. Operations Design

### 2.1 Operation Groups

Operations are organized into logical groups to make the library easier to learn and use:

1. **Core Operations**
    - `Function`: Executes a callable function or method
    - `App`: Executes an app as an operation
2. **Flow Control Operations**
    - `Sequence`: Executes operations in order
    - `Parallel`: Executes operations concurrently
    - `Branch`: Conditionally executes operations based on conditions (formerly "Conditional")
    - `Loop`: Repeats an operation while a condition is true
3. **Timing Operations**
    - `Delay`: Introduces a delay before executing an operation
    - `Timeout`: Adds a timeout to an operation's execution
    - `Retry`: Retries an operation with configurable backoff (new)
4. **Collection Operations**
    - `Map`: Applies an operation to each item in a collection
    - `Reduce`: Aggregates results from a collection using an operation (new)
    - `Filter`: Selectively processes items based on a predicate (new)
5. **Reactive Operations**
    - `Watch`: Executes an operation when state changes
    - `Subscribe`: Long-running operation that reacts to state changes (replaces ReactiveMap operations)
6. **Higher-level Operations (Compound Operations):**
    - Common use cases that are expressed as composition of primitive ops

### 2.2 Consistent Operation Arguments

Every operation follows consistent patterns for arguments:

1. **Primary Arguments**:
    - Every operation takes its primary argument(s) as positional parameters
    - For operations that execute other operations, the operations to execute are always the primary arguments
    - Example: `Sequence(op1, op2, op3, **kwargs)`
2. **Configuration Arguments**:
    - All non-primary arguments are passed as keyword-only parameters
    - Common configuration parameters use the same name across all operations
    - Example: `error_behavior="continue"` instead of mixing `continue_on_error` and `ignore_errors`
3. **Standardized Parameters**:
    - `error_behavior`: Enum with values like "fail", "continue" (consistent across operations)
    - `max_concurrency`: Used wherever concurrency is controllable
4. **State Path Parameters**:
    - All parameters referencing state paths use a consistent naming pattern: `<purpose>_path`
    - Example: `items_path`, `condition_path`, `watch_path`
    - All path parameters use the same type (tuple of strings) without automatic conversion

### 2.3 Operation Behavior Consistency

1. **Lifecycle**:
    - All operations have a clear start and completion state
    - Reactive operations have well-defined termination conditions
    - All operations can be cancelled and properly clean up resources
2. **Error Handling**:
    - Consistent error propagation model across all operations
    - Standardized `error_behavior` parameter with consistent options
    - Errors are logged with consistent detail level and format
3. **Concurrency Control**:
    - Consistent use of `max_concurrency` parameter
    - Explicit documentation of concurrency effects
    - Proper handling of task cancellation and cleanup

## 3. State Management

### 1. Core Philosophy

The state management system is built around several foundational philosophies that inform every aspect of its design:

### Path-Based Hierarchy

At its core, the system treats state as a hierarchical tree of values. 

### Transactional Integrity

Data consistency is fundamental to the design. The transactional model ensures that operations are ACID.

### 2. Design and Mental Model

### Tree-Based State

The entire state store can be visualized as a tree structure:

```
state (root)
├── users
│   ├── user_123 (dictionary node)
│   │   ├── username: "alice"
│   │   ├── email: "alice@example.com"
│   │   ├── settings (dictionary node)
│   │   │   ├── theme: "dark"
│   │   │   └── notifications: true
│   │   └── posts (list node)
│   │       ├── 0: {title: "Hello", content: "..."}
│   │       └── 1: {title: "World", content: "..."}
│   └── user_456 (dictionary node)
│       └── ...
└── config (dictionary node)
    ├── version: "1.0"
    └── features (list node)
        ├── 0: "search"
        ├── 1: "sharing"
        └── 2: "export"

```

Every point in this tree is a **node**. The two primary types of nodes are:

1. **Dictionary Nodes**: Key-value collections where keys are strings
2. **List Nodes**: Ordered collections with integer indices
3. **Primitives**

### Node Characteristics

All nodes, regardless of type, share common traits:

- **Identity**: Each node has a unique path in the tree
- **Existence**: Nodes can be created, checked for existence, and removed
- **Type**: Nodes have a type (dict, list, or value) that can be checked
- **Traversal**: Nodes provide access to their children
- **Conversion**: Nodes can be converted to standard Python objects

Dictionary and list nodes then add type-specific behaviors aligned with their Python counterparts.

### Node Lifecycle

Nodes dynamically come into existence as they're accessed and populated:

1. **Access**: Requesting a node via `state.dict("users")` ensures the path exists
2. **Population**: Setting values creates the necessary structure along the path
3. **Removal**: Deleting a node removes it and all its children

This lazy instantiation model means developers don't need to explicitly create the state structure upfront.

### Path-Based Addressing

Every node is identified by its path - a sequence of string or integer components that navigate from the root to that specific node. Paths function like coordinates in the state tree.

For example, to access Alice's theme setting:

```
["users", "user_123", "settings", "theme"]
```

This addressing scheme is:

- **Consistent**: The same path always points to the same node
- **Composable**: Paths can be built from sub-paths
- **Serializable**: Paths can be easily stored and transmitted

### 3. Interface Model

The interface model closely mirrors Python's built-in types, making it immediately familiar to Python developers.

### Dictionary Interface

The `AsyncStateDictProtocol` and `SyncStateDictProtocol` provide dictionary-like operations:

```python
# Async example
user_dict = await state.dict("users", "user_123")

# Basic operations
await user_dict.set("username", "alice")
username = await user_dict.get("username")
await user_dict.delete("old_field")

# Collection operations
keys = await user_dict.keys()
values = await user_dict.values()
items = await user_dict.items()

# Dictionary-like methods
await user_dict.update({"email": "new@example.com", "level": 5})
await user_dict.setdefault("visits", 0)
value = await user_dict.pop("temporary_field")

# Conversion
python_dict = await user_dict.to_dict()

```

The interface includes all the operations you'd expect from a Python dictionary, making the transition from standard dictionaries nearly seamless.

### List Interface

Similarly, the `AsyncStateListProtocol` and `SyncStateListProtocol` mirror Python's list operations:

```python
# Async example
posts_list = await state.list("users", "user_123", "posts")

# Basic operations
await posts_list.append({"title": "New Post", "content": "..."})
first_post = await posts_list.get(0)
await posts_list.set(1, {"title": "Updated Post", "content": "..."})
await posts_list.delete(2)

# List-specific operations
await posts_list.insert(0, {"title": "Pinned Post", "content": "..."})
await posts_list.extend([post1, post2, post3])
length = await posts_list.length()

# List-like methods
item = await posts_list.pop()

# Conversion
python_list = await posts_list.to_list()

```

Again, the interface closely follows Python's built-in list, making it intuitive for Python developers.

### Higher-Order Operations

Both node types support higher-order operations that apply functions across their elements:

```python
# Apply a transformation function to a value
await state.transform(
    lambda points: points * 2,
    "users", "user_123", "points"
)

# Map a function to each element in a list
await posts_list.map(lambda post: {**post, "modified": True})

# Filter elements
await posts_list.filter(lambda post: len(post["content"]) > 100)

```

These operations make complex state manipulations more expressive and concise.

### Nested Access

Both interfaces provide methods for accessing nested nodes:

```python
# Starting from a dictionary node
user_dict = await state.dict("users", "user_123")

# Access nested structures
settings_dict = await user_dict.dict("settings")
posts_list = await user_dict.list("posts")

# Operations on nested nodes
await settings_dict.set("theme", "light")
await posts_list.append(new_post)

```

This allows for convenient navigation through the state tree without repeatedly specifying full paths.

### 4. Transactions and Subscriptions

### Transactions

Transactions group multiple operations into atomic units:

```python
# Using the context manager pattern (async)
async with await state.transaction() as txn:
    # All operations within this block use the same transaction
    user1 = await state.dict("users", "user_123", txn=txn)
    user2 = await state.dict("users", "user_456", txn=txn)

    points1 = await user1.get("points", default=0)
    points2 = await user2.get("points", default=0)

    # Transfer points
    await user1.set("points", points1 - 100)
    await user2.set("points", points2 + 100)

    # If any operation fails, all changes are rolled back

```

Transaction features include:

- **Atomicity**: All operations succeed or none do
- **Consistency**: The state is never partially updated
- **Isolation**: Transactions don't see each other's uncommitted changes
- **Durability**: Once committed, changes persist even through failures (for persistent backends)

Transactions can be explicitly managed with `begin_transaction()` or implicitly with the context manager pattern.

### Subscriptions

The subscription system allows code to react to state changes:

```python
# Subscribe to changes in user status (async)
async def on_status_change(path):
    path  # ["users", "status"]
    print(f"{path} status changed")

# Subscribe with different depth patterns
# depth=0: exact match only
# depth=1: direct children
# depth=-1: any descendant
subscription = await state.subscribe(
    ("users", "status"),
    on_status_change,
    depth=0
)

# Later, unsubscribe when no longer needed
await state.unsubscribe(subscription)

```

Key subscription features:

- **Depth Control**: Configure how deep in the hierarchy to observe
- **Change Notifications**: Callbacks receive only the path that’s changed
- **Lifecycle Management**: Subscriptions can be created and cleaned up

The subscription mechanism enables reactive programming patterns, allowing UI components, caching layers, or other system parts to stay synchronized with state changes.

## 4. Error Handling Model

### 4.1 Error Types

- `OperationError`: Base class for all operation-related errors
- Specialized errors for specific failure modes:
    - `OperationTimeoutError`: Operation exceeded its time limit
    - `OperationCancelledError`: Operation was explicitly cancelled
    - `StateAccessError`: Error accessing state
    - `OperationConfigError`: Error in operation configuration

### 4.2 Error Propagation

- Standard `error_behavior` with Literal values:
    - `"fail"`: Stop execution and propagate error (default)
    - `"continue"`: Log error but continue execution
- Propagation behavior:
    - in case of exception:
        - Execute `on_fail` op, if it is set
        - Otherwise, error propagates to the parent and is handled according to parent's error behavior
        - Finally, if it reaches to the root, it is raised as regular python exception (meaining, all ops had set error_behavior=fail and no on_fail operation set)

### 4.3 Error Context

- All errors include context about:
    - Where the error occurred (operation type and structural path)
    - What the operation was trying to do
    - State path involved (if applicable)
    - Operation configuration

## 5. Context Passing

### 5.1 Core Principles

- Consistent, immutable context objects passed between operations
- **Unified Context**: Each operation receives a single Context object that provides both execution metadata and state access
- **Proper Scoping**: State access is automatically scoped to the operation's domain
- **Explicit Metadata**: Relevant execution information (keys, indices) is explicitly available
- **Simple Propagation**: Context flows naturally through the operation tree

### 5.2 Context Class Definition

```python
from __future__ import annotations

from typing import Any, Protocol

from .type_vars import OperationT_co, StateDictT_co

__all__ = [
    "ContextProtocol",
]

class ContextProtocol(Protocol[OperationT_co, StateDictT_co]):
    """
    Protocol defining the interface for a context.
    Contexts provide access to state and services during operation execution.
    """

    # --- Properties access methods --- #

    @property
    def scope(self) -> "StateDictT_co":
        """
        Get the scoped state access.

        Returns:
            The scoped state access.
        """
        ...

    @property
    def operation(self) -> OperationT_co:
        """
        Get the operation associated with context.

        Returns:
            The operation.
        """
        ...

    # --- Context attributes access methods --- #

    def __getitem__(self, key: str) -> Any:
        """
        Get an attribute by key.

        Args:
            key: Attribute key

        Returns:
            Attribute value
        """
        ...

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set an attribute by key.

        Args:
            key: Attribute key
            value: Attribute value
        """
        ...

    def __contains__(self, key: str) -> bool:
        """
        Check if an attribute exists.

        Args:
            key: Attribute key

        Returns:
            True if the attribute exists, False otherwise
        """
        ...

    def __delitem__(self, key: str) -> None:
        """
        Delete an attribute by key.

        Args:
            key: Attribute key
        """
        ...
```

## 6. Execution Engine and Services as Extension Points

- Architecture is centralized around a single orchestrator - execution engine.
- Engine provides point of extension - services (e.g. tracing, debugging, cancellation, resume, etc).

```python

class ExecutionEngine(AsyncService):
    """
    Central orchestrator for operation execution.

    Manages the execution of operations, providing them with context
    and access to services. Does not directly implement execution logic
    but delegates to services.
    """

    state: AsyncStateProtocol = UseService()
    executor = UseService(ExecutionService)
    tracing = UseService(TracingService)
```

### Example method: execute

```python

class ExecutionEngine(AsyncService, Generic[StateT, StateDictT]):
    """
    Central orchestrator for operation execution.

    Manages the execution of operations, providing them with context
    and access to services. The engine is the primary entry point for
    executing operations within the framework.

    Attributes:
        state: The state store to use for operations
        executor: Service for executing operations
        tracing: Service for tracing operation execution
    """

    # Services
    state: StateT = UseService()
    executor = UseService(TaskExecutionService)
    tracing = UseService(TracingService)
    logger = UseService(LoggingService)

    async def execute(
        self,
        operation: Operation[StateDictT],
        parent_context: Context[StateDictT] | None = None,
    ) -> None:
        """
        Execute an operation.

        Creates a new context if no parent context is provided, or derives
        a child context from the parent if one is provided.

        Args:
            operation: The operation to execute
            parent_context: Optional parent context to derive from

        Returns:
            The execution task ID

        Raises:
            OperationConfigError: If the operation is invalid
            OperationError: If the operation execution fails
        """
        # Validate operation
        if not isinstance(operation, Operation):
            raise OperationConfigError(f"Expected Operation instance, got {type(operation)}")

        # Set default structural path
        if parent_context is None:
            state_path = ("_",)
        else:
            state_path = parent_context.scope.path

        if inspect.iscoroutinefunction(self.state.dict):
            scope = await self.state.dict(*state_path)
        else:
            scope = self.state.dict(*state_path)

        # Create root context
        context = Context[StateDictT](
            operation,
            cast(StateDictT, scope),
            {},
        )

        # Execute the operation
        await self.exec_operation(context)
```

### Example method 2: diagram

```python

    def render(self, tree: Operation[StateDictT]) -> None:
        """
        Render the execution tree.

        Args:
            tree: The execution tree to render
        """
        for pre, fill, node in anytree.RenderTree(tree):
            print(
                "%s%s %s"
                % (
                    pre,
                    node.__class__.__name__,
                    node._func.__name__ if hasattr(node, "_func") else "",
                )
            )
```

### Protocols

```python
from __future__ import annotations

from typing import Protocol

from .type_vars import (
    ContextT_contra,
    FunctionOperationT_contra,
    OperationT_contra,
    SequenceOperationT_contra,
    SyncContextT_contra,
)

class AsyncExecutorProtocol(
    Protocol[
        ContextT_contra,
        OperationT_contra,
        FunctionOperationT_contra,
        SequenceOperationT_contra,
    ]
):
    """
    Protocol defining the async interface for the execution engine.

    The execution engine is responsible for executing operations and
    providing them with context and services.
    """

    async def execute(
        self,
        operation: OperationT_contra,
        parent_context: ContextT_contra | None = None,
    ) -> None: ...

    async def exec_operation(
        self,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_function(
        self,
        operation: FunctionOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_sequence(
        self,
        operation: SequenceOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

class SyncExecutorProtocol(
    Protocol[
        SyncContextT_contra,
        OperationT_contra,
        FunctionOperationT_contra,
        SequenceOperationT_contra,
    ]
):
    """
    Protocol defining the async interface for the execution engine.

    The execution engine is responsible for executing operations and
    providing them with context and services.
    """

    def execute(
        self,
        operation: OperationT_contra,
        parent_context: SyncContextT_contra | None = None,
    ) -> None: ...

    def exec_operation(
        self,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_function(
        self,
        operation: FunctionOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_sequence(
        self,
        operation: SequenceOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

```

```python
from __future__ import annotations

from typing import Awaitable, Callable, Protocol, runtime_checkable

from .type_vars import ContextT_co, OperationT
from .types import ErrorBehavior

@runtime_checkable
class OperationProtocol(Protocol[OperationT, ContextT_co]):
    @property
    def parent(self) -> OperationT | None: ...

    @parent.setter
    def parent(self, parent: OperationT | None) -> None: ...

    @property
    def children(self) -> tuple[OperationT, ...]: ...

    @children.setter
    def children(self, children: tuple[OperationT, ...]) -> None: ...

@runtime_checkable
class FunctionOperationProtocol(OperationProtocol[OperationT, ContextT_co], Protocol):
    """
    Executes a callable function or method.

    This is the most basic operation, allowing arbitrary async callables
    to be used within the operations framework.

    Args:
        func: The function to execute
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> async def greet(context):
        ...     print(f"Hello from path {context.path}")
        ...
        >>> op = Function(greet)
    """

    def __init__(
        self,
        func: Callable[["ContextT_co"], Awaitable[None]] | Callable[["ContextT_co"], None],
        /,
        *,
        error_behavior: ErrorBehavior = "fail",
        on_fail: OperationT | None = None,
    ) -> None:
        """
        Initialize the Function operation.

        Args:
            func: The function to execute
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If func is not a callable
        """

@runtime_checkable
class SequenceOperationProtocol(OperationProtocol[OperationT, ContextT_co], Protocol):
    """
    Executes operations in sequential order.

    This operation runs each child operation in sequence, waiting for
    each to complete before executing the next.

    Args:
        *ops: The operations to execute in sequence
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> op1 = Function(func1)
        >>> op2 = Function(func2)
        >>> op3 = Function(func3)
        >>> sequence = Sequence(op1, op2, op3)
    """

    def __init__(
        self,
        op: OperationT,
        /,
        *ops: OperationT,
        error_behavior: ErrorBehavior = "fail",
        on_fail: OperationT | None = None,
    ) -> None:
        """
        Initialize the Sequence operation.

        Args:
            op: The first operation to execute
            *ops: Additional operations to execute in sequence
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If no operations are provided
        """

```

### Project Structure

```
- engine.py (main executor engine)
- errors.py (error types and possibly behavior)
- exceptions.py
- context.py (runtime context)
- services/
	- tracing
	- executor
	- ...
- operations/
	- base
	- core/
		- function
		- app
	- reactive/
		...
	- ...
- + misc...
```

## 7. Implementation Guidelines

### 7.1 Code Structure

- Operations inherit from a common base with minimal required implementation
- Shared utilities for common patterns (error handling, logging, etc.)
- Clear separation between operation interface and implementation

### 72 Documentation Standards

- Every operation has consistent documentation:
    - Purpose and use cases
    - Parameters with types and default values
    - Error handling behavior
    - Example with common pattern

## 8. Operations Interface

```python
CORE

# Function operation
ops.Function(
    func: callable[[context], awaitable[None]],
    /,
    *,

    error_behavior: Literal["fail", "continue"] = "fail",
    on_fail: OperationProtocol | None = None,
)

# App operation
ops.App(
    app: App,
    /,
    *,

    state_path: tuple[str, ...] | str | None = None,

    error_behavior: Literal["fail", "continue"] = "fail",
    on_fail: OperationProtocol | None = None,
)

FLOW CONTROL

# Run in a sequence
ops.Sequence(
	op: OperationProtocol,
	/, 
	*ops: OperationProtocol,

    error_behavior: Literal["fail", "continue"] = "fail",
    on_fail: OperationProtocol | None = None,
)

# Run in a parallel
ops.Parallel(
	op: OperationProtocol,
	/, 
	*ops: OperationProtocol,
	max_concurrency: int = ..., # 1 for sequential, >1 for N, -1 for unlimit

    error_behavior: Literal["fail", "continue"] = "fail",
    on_fail: OperationProtocol | None = None,
)

# Branch based on a state path, condition function
ops.Branch(
	ops: dict[str | bool | int, OperationProtocol] # {True: Sequence(...), False: Parallel(...)}
	/
	*,

    condition: callable[[context], awaitable[Any]] | None = None,
    condition_path: tuple[str, ...] | str | None = None,

    error_behavior: Literal["fail", "continue"] = "fail",
    on_fail: OperationProtocol | None = None,
)

# Loop operation
ops.Loop(
    op: OperationProtocol,
    /,
    *,

    condition: callable[[context], awaitable[bool]] | None = None,
    condition_path: tuple[str, ...] | str | None = None,

    max_iterations: int | None = None,  # if set, iterations are limited to this regardless condition, if only this is set it becomes "how many times to run"
    on_finish=ops.Function(finalize),

    error_behavior: Literal["fail", "continue"] = "fail",
    on_fail: OperationProtocol | None = None,
)

TIMING

# Delay operation
ops.Delay(
    delay: float | callable[[context], awaitable[float]] | None = None,
    delay_path: tuple[str, ...] | str | None = None,
)

# Timeout operation
ops.Timeout(
	op: OperationProtocol,
    timeout=30.0,
    on_timeout: OperationProtocol | None = None,
)

# Retry operation
ops.Retry(
	op: OperationProtocol,
	/, 
	*, 
    max_attempts=3,
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=30.0,
    retry_on=[NetworkError, TimeoutError]
)

COLLECTIONS

# Map operation
map_op = ops.Map(
	op: OperationProtocol,
	/, 
	*, 
    items_path: tuple[str, ...] | str,
    max_concurrency=5,

    error_behavior: Literal["fail", "continue", "retry"] = "fail",
    on_fail: OperationProtocol | None = None,
)

# Reduce operation
# Implement later

# New: Filter operation
# Implement later

REACTIVES

# Wait until key changes
Subscribe(
    op: Operation[StateDictT],
    /,
    *,
    watch_path: Tuple[str, ...] | str,  # Path to watch for changes
    depth: int = 0,  # 0=exact match, 1=direct children, -1=any descendant
    once: bool = False,  # When True, executes once then completes
    max_concurrency: int = 1,  # For handling multiple changes
    ignore_self_changes: bool = False,  # Don't react to own changes
    error_behavior: ErrorBehavior = "fail",
    on_fail: Optional[Operation[StateDictT]] = None,
)
Behavior:

Monitors state at watch_path with specified depth
Executes op when changes occur with change information in context
With once=True, becomes a one-time synchronization point (like "WaitChange")
Configurable concurrency for handling changes

Channel Operation (for inter-component communication):
Channel(
    op: Operation[StateDictT],
    /,
    *,
    channel_path: Tuple[str, ...] | str,  # Path for the channel
    mode: Literal["consumer", "producer", "duplex"] = "consumer",
    max_concurrency: int = 1,
    error_behavior: ErrorBehavior = "fail",
    on_fail: Optional[Operation[StateDictT]] = None,
)
Behavior:

Specialized version of Subscribe focused on communication
In consumer mode: reacts to changes but ignores self-changes
In producer mode: only produces changes
In duplex mode: both produces and consumes with proper isolation
Optimized for cross-component and potentially cross-process communication

HIGHER-LEVEL / COMPOUND

# Special case of Branch - logical condition
ops.Conditional(
	/,
	*,

    if_true: OperationProtocol,
    if_false: OperationProtocol,

    condition: callable[[context], awaitable[bool]] | None = None,
    condition_path: tuple[str, ...] | str | None = None,

    error_behavior: Literal["fail", "continue", "retry"] = "fail",
    on_fail: OperationProtocol | None = None,
):
	return ops.Branch({True: if_true, False: if_false}, condition=condition, condition_path=condition_path)

# Delayed function exec
ops.DelayedFunction(
	op: OperationProtocol,
	/, 
	*, 
	delay: float | callable[[context], awaitable[float]] | None = None,
    delay_path: tuple[str, ...] | str | None = None,
    delay_before: bool = False,
    delay_after: bool = True,  # Or combine these two into one
):
	if delay_after: return ops.Sequence(op, ops.Delay(...))
	if before: return ops.Sequence(ops.Delay(...), op)

def MapSubscribe(
    op: Operation[StateDictT],
    watch_path: Tuple[str, ...] | str,
    max_concurrency: int = 1,
    error_behavior: ErrorBehavior = "fail",
) -> Operation[StateDictT]:
    """Creates a subscription that maps an operation to new items."""
    # Implementation would create a Subscribe that executes a Map
    # This is a composite operation, not a primitive
    return Subscribe(
        Map(op, items_path=watch_path, max_concurrency=max_concurrency),
        watch_path=watch_path,
        depth=1,
        ignore_self_changes=True,
        error_behavior=error_behavior,
    )
    
# Mixture of Subscribe and App
ops.SubscribeApp(...):
	ops.Subscribe(ops.App(app, ...), ...)

# Mixture of Map and App
ops.MapApps(...)

# Mixture of Map and Apps and then subscription based app mapping
ops.MapAppsReactive(...)
```