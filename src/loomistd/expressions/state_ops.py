from __future__ import annotations

from frozendict import frozendict

from loomi.evaluator import Context, Evaluator, Expression, ExpressionPath, ExpressionValue
from loomi.state import ListView


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
        Set(("config", "timeout"), 30)

        # Copy value from another path
        Set(("backup", "user_count"), ("stats", "active_users"))
        ```
    """

    def __init__(self, path: ExpressionPath, value: ExpressionValue, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.value = value

    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """Set value at state path using unified infrastructure."""
        with evaluator.state.transaction() as transaction:
            view, path = self._resolve_path(self.path, evaluator.state, transaction, context)
            value = self._resolve_value(self.value, evaluator.state, transaction, context)
            view.set(path, value)  # type: ignore


class Print(Expression):
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

    def __init__(self, path: ExpressionValue, *, message: str = "{value}", **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.message = message

    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """Print value using unified infrastructure."""
        # Use snapshot context for read-only operation
        with evaluator.state.snapshot() as snapshot:
            value = self._resolve_value(self.path, evaluator.state, snapshot, context)

        # Print the value
        formatted_message = self.message.format(value=value)
        print(formatted_message)


class MapList(Expression):
    """
    Map an expression over a state path.
    This expression allows applying a sub-expression to each item in a list or dictionary at a given state path.
    Note: name is mandatory for key identification.

    Args:
        path: State path to map over (e.g., "users.alice.langs")
        expression: Expression to apply to each item
        name: Optional name for the mapping operation
    """

    def __init__(self, path: ExpressionPath, expression: Expression, name: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.path = path
        self.expression = expression

    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """Map the expression over the state path."""
        with evaluator.state.snapshot() as snapshot:
            view, path = self._resolve_path(self.path, evaluator.state, snapshot, context)

            view = view.list_view(path)  # type: ignore

            if not isinstance(view, ListView):
                raise ValueError(f"Expected ListView for mapping, got {type(view).__name__}")

            for i in range(view.length()):
                child_context = context.derive(
                    expression=self.expression, attributes=frozendict({self.name: {"index": i}})
                )

                # Evaluate the expression for each item
                evaluator.evaluate(self.expression, child_context)
