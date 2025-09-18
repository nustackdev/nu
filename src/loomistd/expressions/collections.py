from __future__ import annotations

from loomi.expression import Context, Expression, ExpressionPath, ExpressionValue
from loomi.tree import ListView

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
        name: Name for the mapping operation
    """

    name: str

    def __init__(
        self,
        app,
        path: ExpressionPath,
        expression: Expression,
        name: str,
        start: ExpressionValue | None = None,
        end: ExpressionValue | None = None,
        **kwargs,
    ):
        super().__init__(app, name=name, **kwargs)
        self.path = path
        self.expression = expression
        self.start = start
        self.end = end

    def do_evaluate(self, context: "Context") -> None:
        """Map the expression over the state path."""
        with self.app.state.tree.snapshot() as snapshot:
            view, path = self._resolve_path(self.path, self.app.state.tree, snapshot, context)
            start = self._resolve_value(self.start, self.app.state.tree, snapshot, context)
            end = self._resolve_value(self.end, self.app.state.tree, snapshot, context)

            view = view.list_view(path)  # type: ignore

            if not isinstance(view, ListView):
                raise ValueError(f"Expected ListView for mapping, got {type(view).__name__}")

            for i in range(start, end or view.length()):
                child_context = self._create_child_context(
                    context,
                    child_expression=self.expression,
                    child_attributes={self.name: {"index": i}},
                )

                # Evaluate the expression for each item
                self.expression.evaluate(child_context)
