from __future__ import annotations

from scriptable.app.exceptions import AppError

__all__ = [
    "ModelError",
    "ModelTransactionError",
]


class ModelError(AppError):
    """Base class for model system errors."""

    pass


class ModelTransactionError(ModelError):
    """Raised for transaction-related errors."""

    pass
