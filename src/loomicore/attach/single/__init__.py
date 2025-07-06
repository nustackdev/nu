"""
Single resource attachment pattern.

This module provides the Attach() function for declaring single resource
dependencies in resource classes. It represents the most basic attach pattern
where one descriptor resolves to exactly one resource instance.
"""

from __future__ import annotations

from .descriptor import Attach, ResourceDescriptor

__all__ = [
    "ResourceDescriptor",
    "Attach",
]
