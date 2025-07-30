"""
Type definitions for the path module.

This module defines the core types and protocols used in path operations,
providing clear interfaces and type safety for path construction and evaluation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from .variable import Variable

__all__ = [
    "PathComponent",
    "PathResult",
]

# Basic path types
PathComponent = str | int
ExtendedPathComponent: TypeAlias = "PathComponent | Variable"
"""A single component of a path - a string key, integer index, or variable reference."""

PathResult = Any
"""Result of evaluating a path - can be any value from the tree."""
