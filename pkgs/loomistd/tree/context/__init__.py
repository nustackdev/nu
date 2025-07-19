"""
Context management for tree operations.

This module provides unified context handling for both transactions and snapshots,
replacing the previous transaction-only approach with a more flexible system.
"""

from .context_managers import (
    create_context,
    create_view_context_manager,
    with_context,
    with_snapshot,
    with_transaction,
)
from .contextual_base import ContextualBase, is_contextual
from .protocols import (
    ContextProtocol,
    ContextType,
    SnapshotContextProtocol,
    TransactionContextProtocol,
)

__all__ = [
    # Base classes
    "ContextualBase",
    "is_contextual",
    # Context managers
    "create_context",
    "create_view_context_manager",
    "with_context",
    "with_snapshot",
    "with_transaction",
    # Protocols
    "ContextProtocol",
    "ContextType",
    "SnapshotContextProtocol",
    "TransactionContextProtocol",
]
