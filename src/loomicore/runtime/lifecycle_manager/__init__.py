"""
Lifecycle Manager - Centralized resource lifecycle and state management.

This package provides the LifecycleManager which handles all resource lifecycle
operations including state transitions, hook execution, and dependency coordination.

Classes:
    LifecycleManager: Main lifecycle management implementation

Exceptions:
    LifecycleError: Base exception for lifecycle operations
    StateTransitionError: Exception for invalid state transitions

The LifecycleManager serves as the central authority for resource state management
in the runtime system, owning state storage and coordinating with other runtime
components for complete lifecycle operations.
"""

from __future__ import annotations

from .exceptions import LifecycleError, StateTransitionError
from .manager import LifecycleManager

__all__ = [
    "LifecycleManager",
    "LifecycleError",
    "StateTransitionError",
]
