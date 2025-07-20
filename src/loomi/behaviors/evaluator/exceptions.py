from __future__ import annotations

__all__ = [
    "EvaluatorError",
    "EvaluationError",
]


class EvaluatorError(Exception):
    """Base exception for evaluator errors."""

    pass


class EvaluationError(EvaluatorError):
    """Exception raised when evaluation fails."""

    pass
