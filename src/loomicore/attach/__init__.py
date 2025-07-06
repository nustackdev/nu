"""
Attach patterns for declarative resource dependencies.

This package provides the attach descriptor system that enables declarative
dependency injection in Loomi resources. Each pattern handles a different
type of resource relationship and coordination.

Available Patterns:
    - Attach(): Single resource attachment
    - AttachMany(): Homogeneous resource list with load balancing (future)

The attach system uses self-resolving descriptors that integrate cleanly
with the runtime composition engine without requiring pattern-specific
logic in core components.
"""

from __future__ import annotations

# Core components
from .base_descriptor import BaseResourceDescriptor

# Resource attachment patterns
from .many import AttachMany, ListCoordinator
from .single import Attach

__all__ = [
    # Core
    "BaseResourceDescriptor",
    # Single resource attachment
    "Attach",
    # Many patterns
    "AttachMany",
    "ListCoordinator",
]
