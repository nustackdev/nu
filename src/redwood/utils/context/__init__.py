"""Context management for tree operations.

This module provides unified context handling for both transactions and snapshots.
"""

from .context_managers import create_context, with_context
from .contextual_base import ContextualBase, is_contextual


__all__ = [
    "ContextualBase",
    "create_context",
    "is_contextual",
    "with_context",
]
