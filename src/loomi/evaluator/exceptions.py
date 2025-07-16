from __future__ import annotations

__all__ = [
    "EvaluatorError",
    "EvaluationError",
    "EvaluatorNotFoundError",
]


class EvaluatorError(Exception):
    """Base exception for evaluator errors."""

    pass


class EvaluationError(EvaluatorError):
    """Exception raised when evaluation fails."""

    pass


class EvaluatorNotFoundError(EvaluatorError):
    """Exception raised when no evaluator found for expression type."""

    pass
