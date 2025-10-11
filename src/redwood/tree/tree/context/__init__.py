"""Context management for tree operations.

This module provides unified context handling for both transactions and snapshots,
replacing the previous transaction-only approach with a more flexible system.
"""

from .context_managers import create_context, with_context
from .contextual_base import ContextualBase, is_contextual
from .protocols import (
    ContextProtocol,
    ContextType,
    SnapshotContextProtocol,
    TransactionContextProtocol,
)


__all__ = [
    # Protocols
    "ContextProtocol",
    "ContextType",
    # Base classes
    "ContextualBase",
    "SnapshotContextProtocol",
    "TransactionContextProtocol",
    # Context managers
    "create_context",
    "is_contextual",
    "with_context",
]
