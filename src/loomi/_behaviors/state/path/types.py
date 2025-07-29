"""
Type definitions for the path module.

This module defines the core types and protocols used in path operations,
providing clear interfaces and type safety for path construction and evaluation.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "PathComponent",
    "PathResult",
]

# Basic path types
PathComponent = str | int
"""A single component of a path - either a string key or integer index."""

PathResult = Any
"""Result of evaluating a path - can be any value from the tree."""
