"""
Utilities for the state management system.

This module contains shared utilities and helper functions used throughout
the state management system, including:
- Empty sentinel for distinguishing between None and nonexistent values
- Transaction context management
- Type guards and helpers
"""

from __future__ import annotations

from typing import Any, TypeGuard


class Empty:
    """
    Sentinel object representing an empty value, distinct from None.

    Used for distinguishing between a legitimate None value and a
    nonexistent value in operations that may return None normally.
    """

    def __repr__(self) -> str:
        """String representation for debugging."""
        return "<Empty>"

    def __str__(self) -> str:
        """String representation for display."""
        return "Empty"

    def __bool__(self) -> bool:
        """Boolean evaluation, always False."""
        return False


def is_empty(value: Any) -> TypeGuard[Empty]:
    """
    Check if a value is the EMPTY sentinel.

    Args:
        value: Value to check

    Returns:
        True if value is the EMPTY sentinel, False otherwise
    """
    return isinstance(value, Empty)
