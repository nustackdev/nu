from __future__ import annotations

from loomi.expression import Context, Expression, ExpressionError, ExpressionPath, ExpressionValue
from loomistd.app import SyncAppProtocol

__all__ = [
    "Set",
    "Print",
    "IncrementInt",
    "DecrementInt",
]


class Set(Expression[SyncAppProtocol]):
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
        Set(("config", "timeout"), 30)

        # Copy value from another path
        Set(("backup", "user_count"), ("stats", "active_users"))
        ```
    """

    def __init__(self, app, path: ExpressionPath, value: ExpressionValue, **kwargs):
        super().__init__(app, **kwargs)
        self.path = path
        self.value = value

    def do_evaluate(self, context: "Context") -> None:
        """Set value at state path using unified infrastructure."""
        with self.app.state.tree.transaction() as transaction:
            view, path = self._resolve_path(self.path, self.app.state.tree, transaction, context)
            value = self._resolve_value(self.value, self.app.state.tree, transaction, context)
            view.set(path, value)  # type: ignore


class Print(Expression[SyncAppProtocol]):
    """
    Print a value to stdout with optional formatting.

    Args:
        value: Value to print (can be direct value or state path)
        message: Optional message template (uses {value} placeholder)
    Examples:
        ```python
        # Print direct value
        Print("Hello, World!")

        # Print with custom message
        Print(("stats", "user_count"), message="Active users: {value}")
        ```
    """

    def __init__(self, app, path: ExpressionValue, *, message: str = "{value}", **kwargs):
        super().__init__(app, **kwargs)
        self.path = path
        self.message = message

    def do_evaluate(self, context: "Context") -> None:
        """Print value using unified infrastructure."""
        # Use snapshot context for read-only operation
        with self.app.state.tree.snapshot() as snapshot:
            value = self._resolve_value(self.path, self.app.state.tree, snapshot, context)

        # Print the value
        formatted_message = self.message.format(value=value)
        print(formatted_message)


class IncrementInt(Expression[SyncAppProtocol]):
    """
    Increment an integer value at a state path.

    This expression reads the current value at the given path, increments it
    by the specified amount (default 1), and stores the result back.

    Args:
        path: State path to the integer value (e.g., "counters.users")
        amount: Amount to increment by (can be direct value or state path, default 1)

    Examples:
        ```python
        # Increment by 1 (default)
        IncrementInt(("counters", "page_views"))

        # Increment by specific amount
        IncrementInt(("scores", "player1"), 10)

        # Increment by value from state
        IncrementInt(("totals", "sum"), ("inputs", "delta"))
        ```
    """

    def __init__(self, app, path: ExpressionPath, amount: ExpressionValue = 1, **kwargs):
        super().__init__(app, **kwargs)
        self.path = path
        self.amount = amount

    def do_evaluate(self, context: "Context") -> None:
        """Increment integer value at state path."""
        with self.app.state.tree.transaction() as transaction:
            # Resolve the path and amount
            view, path_key = self._resolve_path(
                self.path, self.app.state.tree, transaction, context
            )
            increment_amount = self._resolve_value(
                self.amount, self.app.state.tree, transaction, context
            )

            # Get current value
            try:
                current_value = view.get(path_key)  # type: ignore
            except Exception as e:
                raise ExpressionError(
                    f"Failed to get current value at path {self.path}: {e}",
                    expression=self,
                    cause=e,
                )

            # Validate types
            if not isinstance(current_value, int):
                raise ExpressionError(
                    f"Current value at {self.path} is not an integer (got {type(current_value).__name__}: {current_value})",
                    expression=self,
                )

            if not isinstance(increment_amount, (int, float)):
                raise ExpressionError(
                    f"Increment amount must be a number (got {type(increment_amount).__name__}: {increment_amount})",
                    expression=self,
                )

            # Calculate new value
            new_value = current_value + int(increment_amount)

            # Store the result
            view.set(path_key, new_value)  # type: ignore

            # logger.debug(
            #     f"Incremented value at {self.path}",
            #     extra={
            #         "old_value": current_value,
            #         "increment_amount": increment_amount,
            #         "new_value": new_value,
            #     },
            # )


class DecrementInt(Expression[SyncAppProtocol]):
    """
    Decrement an integer value at a state path.

    This expression reads the current value at the given path, decrements it
    by the specified amount (default 1), and stores the result back.

    Args:
        path: State path to the integer value (e.g., "counters.users")
        amount: Amount to decrement by (can be direct value or state path, default 1)

    Examples:
        ```python
        # Decrement by 1 (default)
        DecrementInt(("counters", "retries_left"))

        # Decrement by specific amount
        DecrementInt(("health", "player1"), 25)

        # Decrement by value from state
        DecrementInt(("inventory", "gold"), ("costs", "item_price"))
        ```
    """

    def __init__(self, app, path: ExpressionPath, amount: ExpressionValue = 1, **kwargs):
        super().__init__(app, **kwargs)
        self.path = path
        self.amount = amount

    def do_evaluate(self, context: "Context") -> None:
        """Decrement integer value at state path."""
        with self.app.state.tree.transaction() as transaction:
            # Resolve the path and amount
            view, path_key = self._resolve_path(
                self.path, self.app.state.tree, transaction, context
            )
            decrement_amount = self._resolve_value(
                self.amount, self.app.state.tree, transaction, context
            )

            # Get current value
            try:
                current_value = view.get(path_key)  # type: ignore
            except Exception as e:
                raise ExpressionError(
                    f"Failed to get current value at path {self.path}: {e}",
                    expression=self,
                    cause=e,
                )

            # Validate types
            if not isinstance(current_value, int):
                raise ExpressionError(
                    f"Current value at {self.path} is not an integer (got {type(current_value).__name__}: {current_value})",
                    expression=self,
                )

            if not isinstance(decrement_amount, (int, float)):
                raise ExpressionError(
                    f"Decrement amount must be a number (got {type(decrement_amount).__name__}: {decrement_amount})",
                    expression=self,
                )

            # Calculate new value
            new_value = current_value - int(decrement_amount)

            # Store the result
            view.set(path_key, new_value)  # type: ignore

            # logger.debug(
            #     f"Decremented value at {self.path}",
            #     extra={
            #         "old_value": current_value,
            #         "decrement_amount": decrement_amount,
            #         "new_value": new_value,
            #     },
            # )
