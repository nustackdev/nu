"""
Attach patterns for declarative resource dependencies.

This package provides the attach descriptor system that enables declarative
dependency injection in Loomi resources. Each pattern handles a different
type of resource relationship and coordination.

Available Patterns:
    - Attach(): Single resource attachment
    - AttachList(): Homogeneous resource list with indexed access
    - AttachDict(): Homogeneous resource dict with named access

The attach system uses self-resolving descriptors that integrate cleanly
with the runtime composition engine without requiring pattern-specific
logic in core components.
"""

from __future__ import annotations

# Core components
from .base_descriptor import BaseResourceDescriptor

# Resource attachment patterns
from .dict import AttachDict, DictCoordinator
from .exceptions import AttachError
from .list import AttachList, ListCoordinator
from .single import Attach

__all__ = [
    # Core
    "BaseResourceDescriptor",
    "AttachError",
    # Single resource attachment
    "Attach",
    # List patterns
    "AttachList",
    "ListCoordinator",
    # Dict patterns
    "AttachDict",
    "DictCoordinator",
]
