"""
Attach patterns for declarative resource dependencies.

This package provides the attach descriptor system that enables declarative
dependency injection in Loomi resources. Each pattern handles a different
type of resource relationship and coordination.

Available Patterns:
    - Attach(): Single resource attachment
    - AttachMany(): Homogeneous resource list with load balancing (future)
    - AttachManyDict(): Keyed resource dictionary (future)

The attach system uses self-resolving descriptors that integrate cleanly
with the runtime composition engine without requiring pattern-specific
logic in core components.
"""

from __future__ import annotations

# Core components
from .base_descriptor import BaseResourceDescriptor

# Single resource pattern
from .single import Attach, ResourceDescriptor

# Future patterns will be imported here:
# from .many_list import AttachMany, ManyListDescriptor, ListCoordinator
# from .many_dict import AttachManyDict, ManyDictDescriptor, DictCoordinator

__all__ = [
    # Core
    "BaseResourceDescriptor",
    # Single pattern
    "Attach",
    "ResourceDescriptor",
    # Future patterns:
    # "AttachMany",
    # "ManyListDescriptor",
    # "ListCoordinator",
    # "AttachManyDict",
    # "ManyDictDescriptor",
    # "DictCoordinator",
]
