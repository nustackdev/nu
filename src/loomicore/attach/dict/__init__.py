"""
Dict resource attachment pattern.

This module provides the AttachDict() function for declaring multiple homogeneous
resource dependencies in resource classes. It creates a DictCoordinator that
manages a key-value collection of resources with named access.
"""

from __future__ import annotations

from .coordinator import DictCoordinator
from .descriptor import AttachDict, DictDescriptor

__all__ = [
    "AttachDict",
    "DictDescriptor",
    "DictCoordinator",
]
