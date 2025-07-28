from __future__ import annotations

from loomi.evaluator import Context, Evaluator, Expression
from loomi.state import Value


class Set(Expression):
    """
    Set a value at a state path.

    This expression demonstrates the core pattern for state modification:
    - Accept both direct values and state paths
    - Use context managers for storage context management
    - Use lower-level view interface for explicit control
    - Minimal implementation with maximum functionality

    Args:
        path: State path where to store the value (e.g., "users.alice.email")
        value: Value to store (can be direct value or state path)

    Examples:
        ```python
        # Set direct value
        Set("config.timeout", 30)

        # Copy value from another path
        Set("backup.user_count", "stats.active_users")

        # Set complex data
        Set("users.alice", {"name": "Alice", "role": "admin"})

        # With error handling
        Set("critical.setting", "source.value",
            error_behavior="continue",
            on_fail=Print("Failed to set critical setting"))
        ```
    """

    def __init__(self, path: str, value: Value, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.value = value

    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """Set value at state path using unified infrastructure."""
        path_components = self.path.split(".")

        with evaluator.state.at(*path_components[:-1]).with_dict_view() as view:
            view.set(path_components[-1], self.value)


class Print(Expression):
    """
    Print a value to stdout with optional formatting.

    This expression demonstrates read-only operations and flexible value handling:
    - Resolve values from state or use direct values
    - Optional message formatting
    - Production-ready logging integration
    - Snapshot context for read-only operations

    Args:
        value: Value to print (can be direct value or state path)
        message: Optional message template (uses {value} placeholder)
        use_logger: If True, use logger.info instead of print()

    Examples:
        ```python
        # Print direct value
        Print("Hello, World!")

        # Print state value
        Print("users.alice.name")

        # Print with custom message
        Print("stats.user_count", message="Active users: {value}")

        # Print complex data
        Print("config.database", message="DB Config: {value}")
        ```
    """

    def __init__(self, path: str, *, message: str = "{value}", **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.message = message

    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """Print value using unified infrastructure."""
        # Use snapshot context for read-only operation
        path_components = self.path.split(".")

        with evaluator.state.at(*path_components[:-1]).with_dict_view(snapshot=True) as view:
            # Resolve value (could be direct value or state path)
            resolved_value = view.get(path_components[-1], default=None)
            # Format message
            formatted_message = self.message.format(value=resolved_value)

            # Use print for development/debugging
            print(formatted_message)
