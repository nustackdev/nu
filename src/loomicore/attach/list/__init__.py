"""
List resource attachment pattern.

This module provides the AttachList() function for declaring multiple homogeneous
resource dependencies in resource classes. It creates a ListCoordinator that
manages an ordered collection of resources with indexed access.
"""

from __future__ import annotations

from .coordinator import ListCoordinator
from .descriptor import AttachList, ListDescriptor

__all__ = [
    "AttachList",
    "ListDescriptor",
    "ListCoordinator",
]
