# File: attach/many_list/__init__.py
"""
Many list resource attachment pattern.

This module provides the AttachMany() function for declaring multiple homogeneous
resource dependencies in resource classes. It creates a ListCoordinator that
manages an ordered collection of resources with indexed access.
"""

from __future__ import annotations

from .coordinator import ListCoordinator
from .descriptor import AttachMany, ManyListDescriptor

__all__ = [
    "AttachMany",
    "ManyListDescriptor",
    "ListCoordinator",
]
