"""
Path module for tree navigation.

This module provides pure path construction and evaluation functionality
for navigating through tree structures. Paths are immutable objects that
represent navigation routes without any query logic or operations.

TODO: refactor this to use the new view management system.

Core Components:
- Path: Main class for path construction and evaluation
- PathResolver: Handles resolution of paths against tree data
- PathProtocol: Interface for path-like objects
- Path exceptions: Comprehensive error handling
"""

from .exceptions import PathConstructionError, PathError, PathEvaluationError, PathNotFoundError
from .path import ExtendedPath, Path, _Path
from .resolver import PathResolver
from .types import PathComponent, PathResult

__all__ = [
    # Core classes
    "_Path",
    "Path",
    "ExtendedPath",
    "PathResolver",
    # Types and protocols
    "PathComponent",
    "PathResult",
    # Exceptions
    "PathError",
    "PathConstructionError",
    "PathEvaluationError",
    "PathNotFoundError",
]
