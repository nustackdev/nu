from __future__ import annotations

from frozendict import frozendict

from loomi.app import AppBase
from loomi.evaluator import Context, Expression, ExpressionPath
from loomi.state import ListView

__all__ = [
    "MapList",
]


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

    def do_evaluate(self, app: AppBase, context: "Context") -> None:
        """Map the expression over the state path."""
        with app.state.tree.snapshot() as snapshot:
            view, path = self._resolve_path(self.path, app.state.tree, snapshot, context)

            view = view.list_view(path)  # type: ignore

            if not isinstance(view, ListView):
                raise ValueError(f"Expected ListView for mapping, got {type(view).__name__}")

            for i in range(view.length()):
                child_context = context.derive(
                    expression=self.expression, attributes=frozendict({self.name: {"index": i}})
                )

                # Evaluate the expression for each item
                app.evaluator.evaluate(app, self.expression, child_context)
